package ai.stromex.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * StromeX's Android shell: a single Activity hosting a WebView that renders
 * the same Next.js static-export bundle shipped to the browser, served from
 * a virtual HTTPS origin rather than file:// — WebView's fetch()/CORS
 * behavior for file:// origins is unreliable (fetch requests send
 * `Origin: null`, which most CORS configurations reject), so the app's own
 * assets are served locally through {@link #shouldInterceptRequest} under
 * {@code https://stromex.local/}, the same pattern Capacitor's own
 * WebViewAssetLoader uses — reimplemented here with plain framework APIs
 * (no androidx.webkit) because this build environment cannot reach
 * Google's Maven repository to fetch that dependency. Everything used here
 * (android.app.Activity, android.webkit.*) ships in the Android platform
 * itself, requiring no external library at all.
 */
public class MainActivity extends Activity {

    private static final String VIRTUAL_HOST = "stromex.local";
    private static final String START_URL = "https://" + VIRTUAL_HOST + "/index.html";
    // Must match the intent-filter in AndroidManifest.xml and the backend's
    // APP_DEEP_LINK_SCHEME setting (see app/core/config.py) — this is where
    // POST-code-exchange /auth/google/callback sends the system browser once
    // sign-in with Google succeeds.
    private static final String AUTH_CALLBACK_SCHEME = "ai.stromex.app";
    private static final String AUTH_CALLBACK_HOST = "auth-callback";

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (VIRTUAL_HOST.equals(uri.getHost())) {
                    return serveAsset(uri.getPath());
                }
                return null; // let the network handle everything else (the real API calls)
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (VIRTUAL_HOST.equals(uri.getHost())) {
                    return false; // keep in-app navigation inside the WebView
                }
                // Anything else — an external link, or Google's own sign-in
                // pages — opens in the system browser rather than navigating
                // the app's WebView there. This isn't just a UX choice:
                // Google's terms disallow completing sign-in inside an
                // embedded WebView at all, so this is the one legitimate way
                // "Continue with Google" can work from this app.
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
                return true;
            }
        });

        webView.loadUrl(START_URL);
        handleIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    /**
     * Recognizes the Google Sign-In callback deep link
     * (ai.stromex.app://auth-callback?access_token=...&refresh_token=...),
     * pulled in by the intent-filter in AndroidManifest.xml once the system
     * browser finishes the OAuth round trip. Everything else (a cold app
     * launch with no special intent) is a no-op.
     */
    private void handleIntent(Intent intent) {
        if (intent == null) return;
        Uri uri = intent.getData();
        if (uri == null || !AUTH_CALLBACK_SCHEME.equals(uri.getScheme())
                || !AUTH_CALLBACK_HOST.equals(uri.getHost())) {
            return;
        }

        String accessToken = uri.getQueryParameter("access_token");
        String refreshToken = uri.getQueryParameter("refresh_token");
        if (accessToken == null || refreshToken == null) {
            return;
        }

        // Same localStorage keys apps/web/src/lib/auth-storage.ts uses, so
        // the web app's own auth state (useAuth.hydrate()) picks these up
        // exactly as if it had called POST /auth/login itself.
        String script = "localStorage.setItem('stromex.access_token', " + JSONObject.quote(accessToken) + ");"
                + "localStorage.setItem('stromex.refresh_token', " + JSONObject.quote(refreshToken) + ");"
                + "location.href = 'https://" + VIRTUAL_HOST + "/chat.html';";
        webView.evaluateJavascript(script, null);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private WebResourceResponse serveAsset(String path) {
        if (path == null || path.isEmpty() || path.equals("/")) {
            path = "/index.html";
        }
        String assetPath = path.startsWith("/") ? path.substring(1) : path;

        for (String candidate : candidatePaths(assetPath)) {
            try {
                InputStream stream = getAssets().open(candidate);
                return new WebResourceResponse(mimeTypeFor(candidate), "utf-8", stream);
            } catch (IOException notFound) {
                // try the next candidate mapping
            }
        }
        return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found",
                new HashMap<>(), null);
    }

    /**
     * Next.js's static export writes one real .html file per route
     * (chat.html, books/detail.html, ...) rather than serving every route
     * through a single SPA shell. A deep link or a page reload on, say,
     * "/chat" arrives here with no file extension, so this tries the
     * Next.js export's own naming convention before giving up.
     */
    private String[] candidatePaths(String assetPath) {
        if (assetPath.contains(".")) {
            return new String[]{assetPath};
        }
        String trimmed = assetPath.endsWith("/") ? assetPath.substring(0, assetPath.length() - 1) : assetPath;
        return new String[]{
                trimmed + ".html",
                trimmed + "/index.html",
                trimmed,
        };
    }

    private String mimeTypeFor(String path) {
        String lower = path.toLowerCase(java.util.Locale.ROOT);
        Map<String, String> types = MIME_TYPES;
        for (Map.Entry<String, String> entry : types.entrySet()) {
            if (lower.endsWith(entry.getKey())) {
                return entry.getValue();
            }
        }
        return "application/octet-stream";
    }

    private static final Map<String, String> MIME_TYPES = new HashMap<>();
    static {
        MIME_TYPES.put(".html", "text/html");
        MIME_TYPES.put(".js", "application/javascript");
        MIME_TYPES.put(".css", "text/css");
        MIME_TYPES.put(".json", "application/json");
        MIME_TYPES.put(".woff2", "font/woff2");
        MIME_TYPES.put(".woff", "font/woff");
        MIME_TYPES.put(".svg", "image/svg+xml");
        MIME_TYPES.put(".png", "image/png");
        MIME_TYPES.put(".ico", "image/x-icon");
        MIME_TYPES.put(".txt", "text/plain");
    }
}
