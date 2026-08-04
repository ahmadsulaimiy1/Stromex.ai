package ai.sautiy

import ai.sautiy.ui.theme.SautiyTheme
import ai.sautiy.ui.workspace.SautiyWorkspace
import ai.sautiy.ui.workspace.WorkspaceViewModel
import android.Manifest
import android.app.Application
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * The only Activity in SAUTIY.
 *
 * That is not a simplification — it is chapter 4.1. One canvas means one Activity, no
 * navigation graph and no back stack of destinations. Settings and About are the two full
 * destinations the Bible allows, and they are composables over the same window, so returning
 * from them restores the workspace exactly as it was.
 */
class SautiyActivity : ComponentActivity() {

    private var pendingRecordRequest = false

    /**
     * Chapter 3.2.1: the microphone is requested **at the moment of the first record tap**, not
     * on launch. A permission dialog before the user has expressed any intent is a wall in
     * front of a product they have not seen yet, and it is the single most common reason a
     * first-time user never reaches the record control at all.
     */
    private val requestMicrophone = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted && pendingRecordRequest) {
            pendingRecordRequest = false
            viewModelRef?.actions?.onRecordOrStop?.invoke()
        }
    }

    private var viewModelRef: WorkspaceViewModel? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        // Installed before super.onCreate so the splash theme is genuinely the first frame and
        // there is no seam between it and the workspace (chapter 2.8).
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)

        setContent {
            SautiyTheme {
                val model: WorkspaceViewModel = viewModel()
                viewModelRef = model
                val state by model.state.collectAsState()

                SautiyWorkspace(
                    state = state,
                    actions = model.actions.copy(
                        onRecordOrStop = {
                            if (hasMicrophonePermission()) {
                                model.actions.onRecordOrStop()
                            } else {
                                pendingRecordRequest = true
                                requestMicrophone.launch(Manifest.permission.RECORD_AUDIO)
                            }
                        },
                    ),
                    modifier = Modifier
                        .fillMaxSize()
                        // Edge to edge, but never underneath the system bars: the transport dock
                        // sits in the natural thumb zone and a gesture bar over it would make the
                        // record control unreachable.
                        .windowInsetsPadding(WindowInsets.systemBars),
                )
            }
        }
    }

    private fun hasMicrophonePermission(): Boolean =
        ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
}

/**
 * The application object.
 *
 * It registers the platform-backed encoders with the core's registry. The core deliberately
 * knows nothing about Android, so this is where a format that needs a device becomes available
 * — and if registration fails, the export panel simply does not offer that format, rather than
 * offering it and then failing (chapter 14).
 */
class SautiyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        ai.sautiy.export.PlatformEncoders.registerAll()
    }
}
