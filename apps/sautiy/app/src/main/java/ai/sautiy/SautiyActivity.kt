package ai.sautiy

import ai.sautiy.ui.theme.SautiyTheme
import ai.sautiy.ui.workspace.SautiyWorkspace
import ai.sautiy.ui.workspace.WorkspaceViewModel
import android.Manifest
import android.app.Activity
import android.app.Application
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContract
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

    /**
     * The destination picker — Storage Access Framework, not a storage permission.
     *
     * SAUTIY never asks for READ/WRITE_EXTERNAL_STORAGE. The user points at a place, the system
     * hands back a writable document, and that place can be internal storage, an SD card or a
     * cloud provider without this application knowing or caring which. That is both the only
     * route Android still supports and the one that asks the user for the least.
     */
    private val chooseDestination = registerForActivityResult(SaveAudioDocument()) { uri ->
        val model = viewModelRef ?: return@registerForActivityResult
        if (uri == null) model.exportCancelled() else model.exportTo(uri)
    }

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
                        // Export is one action: the picker opens on the tap, and the file is
                        // written where the user pointed. There is no intermediate "exported to
                        // somewhere, now find it" step.
                        onExport = {
                            chooseDestination.launch(
                                SaveAudioDocument.Request(
                                    mimeType = state.exportFormat.mimeType,
                                    fileName = model.suggestedExportName,
                                ),
                            )
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
 * Creates a document with a MIME type chosen at launch time.
 *
 * `ActivityResultContracts.CreateDocument` fixes its MIME type when the contract is registered,
 * and SAUTIY does not know at that point whether the user will export MP3 or FLAC. Declaring
 * the wrong type matters: it is what the picker uses to decide which providers can accept the
 * file, so a wrong one quietly hides destinations the user has.
 */
class SaveAudioDocument : ActivityResultContract<SaveAudioDocument.Request, Uri?>() {

    data class Request(val mimeType: String, val fileName: String)

    override fun createIntent(context: Context, input: Request): Intent =
        Intent(Intent.ACTION_CREATE_DOCUMENT)
            .addCategory(Intent.CATEGORY_OPENABLE)
            .setType(input.mimeType)
            .putExtra(Intent.EXTRA_TITLE, input.fileName)

    override fun parseResult(resultCode: Int, intent: Intent?): Uri? =
        intent.takeIf { resultCode == Activity.RESULT_OK }?.data
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
