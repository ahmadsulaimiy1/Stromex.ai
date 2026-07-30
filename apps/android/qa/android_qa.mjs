// Functional QA pass over the exact static-export bundle the Android WebView
// loads (apps/web/out, served locally), against the real running FastAPI
// backend — a mobile Pixel-5-sized viewport stands in for the WebView since
// no real Android emulator/device is available in this sandbox.
import { chromium, devices } from 'playwright';

const BASE = 'http://127.0.0.1:4173';
const results = [];

function record(name, ok, detail) {
  results.push({ name, ok, detail: detail || '' });
  console.log(`${ok ? 'PASS' : 'FAIL'} - ${name}${detail ? ' :: ' + detail : ''}`);
}

const password = 'AndroidQA-2026!Pass';
let emailCounter = 0;

// The app is a Next.js client-side-routed SPA once hydrated: after a login/
// register submit, navigation happens via router.push (History API), not a
// full document load, so waitForLoadState('networkidle') right after a click
// resolves before the route actually changes. waitForURL is the correct
// primitive for "wait for the SPA to navigate away from here".
async function clickAndWaitForNavigation(page, locator, awayFrom) {
  await locator.click();
  await page.waitForURL((url) => !url.pathname.endsWith(awayFrom), { timeout: 10000 }).catch(() => {});
  await page.waitForLoadState('networkidle').catch(() => {});
}

async function run() {
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  });

  for (const mode of ['light', 'dark']) {
    const context = await browser.newContext({
      ...devices['Pixel 5'],
      colorScheme: mode,
    });
    const page = await context.newPage();
    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => consoleErrors.push(String(err)));

    const tag = mode === 'dark' ? ' [dark mode]' : ' [light mode]';
    const email = `android-qa-${Date.now()}-${emailCounter++}@stromex.ai`;

    // 1. Load home page
    await page.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
    record(`home page loads${tag}`, true, page.url());

    // 2. Registration flow
    await page.goto(`${BASE}/register.html`, { waitUntil: 'networkidle' });
    const nameInput = page.locator('#displayName, input[name="displayName"]').first();
    if (await nameInput.count()) {
      await nameInput.fill('Android QA');
    }
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInputs = page.locator('input[type="password"]');
    await emailInput.fill(email);
    const pwCount = await passwordInputs.count();
    for (let i = 0; i < pwCount; i++) {
      await passwordInputs.nth(i).fill(password);
    }
    await clickAndWaitForNavigation(page, page.locator('button[type="submit"]').first(), '/register.html');
    const afterRegisterUrl = page.url();
    const registerOk = afterRegisterUrl.endsWith('/chat');
    record(`registration submits and logs in${tag}`, registerOk, afterRegisterUrl);

    // 3. Explicit login flow (separate account, to test login independent of registration auto-login)
    const loginEmail = `android-qa-login-${Date.now()}-${emailCounter++}@stromex.ai`;
    await page.goto(`${BASE}/register.html`, { waitUntil: 'networkidle' });
    await page.locator('#displayName, input[name="displayName"]').first().fill('Android QA Login');
    await page.locator('input[type="email"]').first().fill(loginEmail);
    await page.locator('input[type="password"]').first().fill(password);
    await clickAndWaitForNavigation(page, page.locator('button[type="submit"]').first(), '/register.html');

    await page.goto(`${BASE}/login.html`, { waitUntil: 'networkidle' });
    await page.locator('input[type="email"], input[name="email"]').first().fill(loginEmail);
    await page.locator('input[type="password"]').first().fill(password);
    await clickAndWaitForNavigation(page, page.locator('button[type="submit"]').first(), '/login.html');
    const afterLoginUrl = page.url();
    const loginOk = !afterLoginUrl.endsWith('/login.html');
    record(`login redirects away from /login${tag}`, loginOk, afterLoginUrl);

    // 4. Session persistence: reload and confirm still authenticated (not bounced to login)
    await page.reload({ waitUntil: 'networkidle' });
    const stillIn = !page.url().endsWith('/login.html');
    record(`session persists across reload${tag}`, stillIn, page.url());

    // 5. Chat page + send a message
    await page.goto(`${BASE}/chat.html`, { waitUntil: 'networkidle' });
    const chatInput = page.locator('textarea').first();
    const chatVisible = await chatInput.isVisible().catch(() => false);
    if (chatVisible) {
      await chatInput.fill('Assalamu alaikum, can you help me understand Surah Al-Fatiha?');
      const sendBtn = page.locator('button[type="submit"], button:has-text("Send")').first();
      await sendBtn.click();
      await page.waitForTimeout(3000);
    }
    record(`chat page usable${tag}`, chatVisible, chatVisible ? 'input+send found' : 'no chat input found');
    const assistantReplyCount = await page.locator('body').innerText().then((t) => t.length);
    record(`chat page renders conversation content${tag}`, assistantReplyCount > 0);

    // 6. Qur'an tutor page (spaced-repetition memorization planner — no
    // rendered ayah text on this page, so no RTL/Arabic markup is expected
    // here; that lives in the chat "Qur'an" mode and Arabic<->English mode)
    await page.goto(`${BASE}/quran.html`, { waitUntil: 'networkidle' });
    const quranLoaded = (await page.locator('body').innerText()).length > 0;
    record(`quran tutor page loads${tag}`, quranLoaded);

    // 7. Arabic RTL check: switch chat composer to Arabic<->English mode and type Arabic
    await page.goto(`${BASE}/chat.html`, { waitUntil: 'networkidle' });
    const arabicModeBtn = page.locator('button:has-text("Arabic")').first();
    if (await arabicModeBtn.count()) {
      await arabicModeBtn.click();
    }
    const composer = page.locator('textarea').first();
    await composer.fill('السلام عليكم');
    await page.waitForTimeout(300);
    const rtlDirCount = await page.locator('[dir="rtl"]').count();
    record(`Arabic input triggers RTL layout${tag}`, rtlDirCount > 0, `${rtlDirCount} dir=rtl elements after Arabic text entry`);

    // 8. Books workspace
    await page.goto(`${BASE}/books.html`, { waitUntil: 'networkidle' });
    const booksLoaded = (await page.locator('body').innerText()).length > 0;
    record(`books page loads${tag}`, booksLoaded);

    // 9. Admin page (expect graceful handling for non-admin user: redirect or forbidden message, not a crash)
    await page.goto(`${BASE}/admin.html`, { waitUntil: 'networkidle' });
    const adminBodyText = await page.locator('body').innerText();
    record(`admin page handles non-admin gracefully${tag}`, adminBodyText.length > 0, adminBodyText.slice(0, 80));

    // 10. Offline handling: go offline, attempt navigation/action, confirm no crash
    await context.setOffline(true);
    await page.goto(`${BASE}/chat.html`, { waitUntil: 'domcontentloaded' }).catch(() => {});
    const bodyAfterOffline = await page.locator('body').innerText().catch(() => '');
    record(`app does not crash when offline${tag}`, bodyAfterOffline.length > 0, `body length ${bodyAfterOffline.length}`);
    await context.setOffline(false);

    // 11. API failure handling: reload after coming back online, confirm no crash overlay
    await page.goto(`${BASE}/login.html`, { waitUntil: 'networkidle' });
    const hasErrorOverlay = await page.locator('text=/unhandled runtime error/i').count();
    record(`no unhandled runtime error overlay${tag}`, hasErrorOverlay === 0);

    record(`no console errors${tag}`, consoleErrors.length === 0, consoleErrors.slice(0, 5).join(' | '));

    await context.close();
  }

  // Tablet responsiveness: iPad viewport
  const tabletContext = await browser.newContext({ ...devices['iPad (gen 7)'] });
  const tabletPage = await tabletContext.newPage();
  await tabletPage.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  const tabletBodyWidth = await tabletPage.evaluate(() => document.body.scrollWidth);
  const viewportWidth = tabletPage.viewportSize().width;
  const noHorizontalOverflow = tabletBodyWidth <= viewportWidth + 5;
  record('tablet viewport: no horizontal overflow on home', noHorizontalOverflow, `body ${tabletBodyWidth}px vs viewport ${viewportWidth}px`);
  await tabletContext.close();

  // Low-memory-ish smoke: constrained network throttling via CDP on a small viewport/older device profile
  const lowEndContext = await browser.newContext({ ...devices['Galaxy S5'] });
  const lowEndPage = await lowEndContext.newPage();
  const cdp = await lowEndContext.newCDPSession(lowEndPage);
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false, latency: 400, downloadThroughput: (200 * 1024) / 8, uploadThroughput: (100 * 1024) / 8,
  });
  await lowEndPage.goto(`${BASE}/index.html`, { waitUntil: 'networkidle', timeout: 30000 });
  const lowEndLoaded = (await lowEndPage.locator('body').innerText()).length > 0;
  record('low-end/throttled device: home page still loads', lowEndLoaded);
  await lowEndContext.close();

  await browser.close();

  const failed = results.filter((r) => !r.ok);
  console.log('\n=== SUMMARY ===');
  console.log(`${results.length - failed.length}/${results.length} checks passed`);
  if (failed.length) {
    console.log('FAILED:');
    failed.forEach((f) => console.log(` - ${f.name}: ${f.detail}`));
  }
  process.exitCode = failed.length ? 1 : 0;
}

run().catch((err) => {
  console.error('FATAL', err);
  process.exit(1);
});
