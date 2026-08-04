package ai.sajjil.app

import ai.sajjil.app.ui.SajjilApp
import ai.sajjil.app.ui.theme.SajjilTheme
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        // Drawn behind the status and navigation bars. Compose insets handle the padding, and a
        // full-bleed waveform is worth the extra care.
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        val services = services
        services.playback.connect()

        setContent {
            SajjilTheme {
                SajjilApp(services = services)
            }
        }
    }

    override fun onStart() {
        super.onStart()
        lifecycleScope.launch {
            services.recordingSession.refreshRemainingSpace()
        }
    }

    override fun onDestroy() {
        // The recording session deliberately outlives the activity — a rotation or a trip to
        // another app must not end a take. Only the playback connection is torn down here.
        if (isFinishing) services.playback.release()
        super.onDestroy()
    }
}
