package ai.sajjil.app

import ai.sajjil.app.audio.AudioExporter
import ai.sajjil.app.audio.PlaybackController
import ai.sajjil.app.audio.RecordingSession
import ai.sajjil.app.data.AudioFileStore
import ai.sajjil.app.data.RecordingRepository
import ai.sajjil.app.data.SajjilDatabase
import ai.sajjil.app.data.SettingsStore
import android.app.Application
import android.content.Context
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * The app's dependencies, constructed once.
 *
 * A hand-written container rather than a DI framework. The graph is a dozen objects deep and
 * entirely static; annotation processing and generated components would add build time and a
 * layer of indirection without removing any real complexity.
 */
class Services(context: Context) {

    val fileStore = AudioFileStore(context)
    val database = SajjilDatabase.get(context)
    val settings = SettingsStore(context)
    val exporter = AudioExporter()

    val repository = RecordingRepository(
        database = database,
        fileStore = fileStore,
        exporter = exporter,
    )

    val recordingSession = RecordingSession(
        context = context,
        store = fileStore,
        database = database,
    )

    val playback = PlaybackController(context)
}

class SajjilApplication : Application() {

    lateinit var services: Services
        private set

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onCreate() {
        super.onCreate()
        services = Services(this)

        scope.launch {
            // Recover anything a crash or a system kill left half-written, before the Library is
            // ever shown. A user should never see a recording in a broken state, or be asked what
            // to do about one.
            runCatching { services.recordingSession.recoverInterrupted() }

            // Old share-sheet copies are just that — copies. The originals are untouched.
            runCatching { services.fileStore.pruneExports(System.currentTimeMillis()) }

            services.recordingSession.refreshRemainingSpace()
        }
    }
}

/** Reaches the container from a composable or a ViewModel. */
val Context.services: Services
    get() = (applicationContext as SajjilApplication).services
