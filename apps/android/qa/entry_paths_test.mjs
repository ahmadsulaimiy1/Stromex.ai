import { chromium, devices } from 'playwright';
import { execSync } from 'node:child_process';

const BASE = 'http://127.0.0.1:4173';
const results = [];
function record(name, ok, detail) {
  results.push({ name, ok, detail: detail || '' });
  console.log(`${ok ? 'PASS' : 'FAIL'} - ${name}${detail ? ' :: ' + detail : ''}`);
}

try {
  execSync('redis-cli --scan --pattern "ratelimit:*" | xargs -r redis-cli del', { stdio: 'ignore' });
} catch {}

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });

// === 1. SIGN UP (registration) end-to-end, backend reachable ===
{
  const ctx = await browser.newContext({ ...devices['Pixel 5'] });
  const page = await ctx.newPage();
  const email = `signup-${Date.now()}@stromex.ai`;
  await page.goto(`${BASE}/register.html`, { waitUntil: 'networkidle' });
  await page.locator('#displayName').fill('Sign Up Test');
  await page.locator('input[type="email"]').first().fill(email);
  await page.locator('input[type="password"]').first().fill('SignUpTest-2026!');
  await page.locator('button[type="submit"]').first().click();
  await page.waitForURL((u) => u.pathname.endsWith('/chat'), { timeout: 10000 }).catch(() => {});
  const landedInChat = page.url().endsWith('/chat');
  const bodyText = await page.locator('body').innerText();
  record('SIGN UP: registration creates account and lands in /chat', landedInChat, page.url());
  record('SIGN UP: chat shell renders after registration', bodyText.includes('Sign Up Test'), bodyText.slice(0, 60));
  await page.screenshot({ path: `${process.argv[2]}/evidence-signup-success.png` });

  // Validation error display: duplicate email
  await page.goto(`${BASE}/register.html`, { waitUntil: 'networkidle' });
  await page.locator('#displayName').fill('Duplicate Test');
  await page.locator('input[type="email"]').first().fill(email); // same email again
  await page.locator('input[type="password"]').first().fill('AnotherPassword-2026!');
  await page.locator('button[type="submit"]').first().click();
  await page.waitForTimeout(1500);
  const dupBody = await page.locator('body').innerText();
  record(
    'SIGN UP: duplicate-email validation error displays clearly',
    /already registered/i.test(dupBody),
    dupBody.slice(0, 150),
  );
  await page.screenshot({ path: `${process.argv[2]}/evidence-signup-validation-error.png` });
  await ctx.close();
}

// === 2. SIGN IN end-to-end + session persistence after "restart" ===
{
  const ctx = await browser.newContext({ ...devices['Pixel 5'] });
  const page = await ctx.newPage();
  const email = `signin-${Date.now()}@stromex.ai`;
  const password = 'SignInTest-2026!';

  // Create the account via API directly (isolates the Sign In test from Sign Up)
  await ctx.request.post('http://localhost:8000/api/v1/auth/register', {
    data: { email, password, display_name: 'Sign In Test' },
  });

  await page.goto(`${BASE}/login.html`, { waitUntil: 'networkidle' });
  await page.locator('input[type="email"]').first().fill(email);
  await page.locator('input[type="password"]').first().fill(password);
  await page.locator('button[type="submit"]').first().click();
  await page.waitForURL((u) => !u.pathname.endsWith('/login.html'), { timeout: 10000 }).catch(() => {});
  record('SIGN IN: login succeeds and leaves /login', !page.url().endsWith('/login.html'), page.url());
  await page.screenshot({ path: `${process.argv[2]}/evidence-signin-success.png` });

  const tokenBefore = await page.evaluate(() => localStorage.getItem('stromex.access_token'));
  record('SIGN IN: access token stored client-side', !!tokenBefore);

  // Simulate an app restart: brand-new browser context, tokens carried over
  // manually (this is exactly what localStorage persistence means — a real
  // app restart on a real device keeps the same localStorage automatically).
  const refreshToken = await page.evaluate(() => localStorage.getItem('stromex.refresh_token'));
  await ctx.close();

  const restartCtx = await browser.newContext({ ...devices['Pixel 5'] });
  // Seed localStorage via an init script so the tokens already exist before
  // the page's own JS (and RequireAuth's hydrate-on-mount) ever runs —
  // injecting them after the first load races against hydrate() already
  // having redirected an (at-that-instant) tokenless page to /welcome.
  await restartCtx.addInitScript(
    ({ a, r }) => {
      localStorage.setItem('stromex.access_token', a);
      localStorage.setItem('stromex.refresh_token', r);
    },
    { a: tokenBefore, r: refreshToken },
  );
  const restartPage = await restartCtx.newPage();
  await restartPage.goto(`${BASE}/chat.html`, { waitUntil: 'networkidle' });
  const stillIn = !restartPage.url().endsWith('/welcome') && !restartPage.url().endsWith('/login.html');
  record('SIGN IN: session persists after simulated app restart', stillIn, restartPage.url());
  await restartPage.screenshot({ path: `${process.argv[2]}/evidence-session-persistence.png` });
  await restartCtx.close();
}

// === 3. GUEST MODE — online (backend reachable) ===
{
  const ctx = await browser.newContext({ ...devices['Pixel 5'] });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/welcome.html`, { waitUntil: 'networkidle' });
  const guestBtn = page.locator('button:has-text("Continue as Guest")');
  record('GUEST (online): button is visible on welcome screen', await guestBtn.isVisible());
  await guestBtn.click();
  await page.waitForURL((u) => u.pathname.endsWith('/chat'), { timeout: 10000 }).catch(() => {});
  record('GUEST (online): lands in /chat immediately', page.url().endsWith('/chat'), page.url());
  await page.screenshot({ path: `${process.argv[2]}/evidence-guest-online-success.png` });
  await ctx.close();
}

// === 4. GUEST MODE — backend unreachable (the actual regression this addresses) ===
// Blocks only the backend host, not the whole browsing context: that's what
// "the backend is unreachable" really means for the shipped Android app,
// whose own asset serving (MainActivity.shouldInterceptRequest) is answered
// in-process and never touches a real network socket — unlike this test's
// own stand-in static file server, which a blanket offline simulation would
// incorrectly block too.
{
  const ctx = await browser.newContext({ ...devices['Pixel 5'] });
  await ctx.route('http://localhost:8000/**', (route) => route.abort('internetdisconnected'));
  const page = await ctx.newPage();
  await page.goto(`${BASE}/welcome.html`, { waitUntil: 'networkidle' });
  const guestBtn = page.locator('button:has-text("Continue as Guest")');
  await guestBtn.click();
  await page.waitForURL((u) => u.pathname.endsWith('/chat'), { timeout: 15000 }).catch(() => {});
  const enteredWhileOffline = page.url().endsWith('/chat');
  record(
    'GUEST (OFFLINE): entry is NOT blocked when the backend is unreachable',
    enteredWhileOffline,
    page.url(),
  );
  const offlineBannerVisible = await page
    .locator("text=/Can't reach the StromeX server/i")
    .isVisible()
    .catch(() => false);
  record('GUEST (OFFLINE): offline banner explains why', offlineBannerVisible);
  const composerVisible = await page.locator('textarea').first().isVisible().catch(() => false);
  record('GUEST (OFFLINE): chat composer still renders (app is usable, not blank)', composerVisible);
  await page.screenshot({ path: `${process.argv[2]}/evidence-guest-offline-success.png` });
  await ctx.close();
}

// === 5. LOGIN attempted while backend unreachable: friendly message + guest escape hatch ===
{
  const ctx = await browser.newContext({ ...devices['Pixel 5'] });
  await ctx.route('http://localhost:8000/**', (route) => route.abort('internetdisconnected'));
  const page = await ctx.newPage();
  await page.goto(`${BASE}/login.html`, { waitUntil: 'networkidle' });
  await page.locator('input[type="email"]').first().fill('anyone@stromex.ai');
  await page.locator('input[type="password"]').first().fill('whatever-password');
  await page.locator('button[type="submit"]').first().click();
  await page.waitForTimeout(2000);
  const body = await page.locator('body').innerText();
  record(
    'SIGN IN (backend unreachable): shows a clear "can\'t reach server" message, not a crash',
    /reach|connection|server/i.test(body),
    body.slice(0, 150),
  );
  record(
    'SIGN IN (backend unreachable): offers "continue as a guest" as a way forward',
    /continue as a guest/i.test(body),
  );
  await page.screenshot({ path: `${process.argv[2]}/evidence-signin-offline-message.png` });
  await ctx.close();
}

await browser.close();

const failed = results.filter((r) => !r.ok);
console.log('\n=== SUMMARY ===');
console.log(`${results.length - failed.length}/${results.length} checks passed`);
if (failed.length) {
  console.log('FAILED:');
  failed.forEach((f) => console.log(` - ${f.name}: ${f.detail}`));
}
process.exitCode = failed.length ? 1 : 0;
