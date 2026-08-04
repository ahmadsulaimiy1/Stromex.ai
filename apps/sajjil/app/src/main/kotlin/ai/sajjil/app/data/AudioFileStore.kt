package ai.sajjil.app.data

import ai.sajjil.audio.AudioBuffer
import ai.sajjil.audio.codec.WavBitDepth
import ai.sajjil.audio.codec.WavInfo
import ai.sajjil.audio.codec.WavReader
import ai.sajjil.audio.codec.WavWriter
import android.content.Context
import android.os.StatFs
import java.io.File
import java.io.RandomAccessFile

/**
 * Owns the on-disk audio.
 *
 * Recordings live in the app's private files directory, so they need no storage permission and
 * are removed cleanly when the app is uninstalled. Exports go to the cache directory and are
 * handed out through a FileProvider; a user who wants a copy somewhere permanent picks the
 * destination themselves through the system document picker.
 */
class AudioFileStore(private val context: Context) {

    val recordingsDirectory: File by lazy {
        File(context.filesDir, "recordings").apply { mkdirs() }
    }

    val exportsDirectory: File by lazy {
        File(context.cacheDir, "exports").apply { mkdirs() }
    }

    fun fileFor(fileName: String): File = File(recordingsDirectory, fileName)

    fun exists(fileName: String): Boolean = fileFor(fileName).isFile

    /** A file name that is unique, sorts chronologically, and is safe on every filesystem. */
    fun newRecordingFileName(timestampMillis: Long): String =
        "sajjil-$timestampMillis.wav"

    fun read(fileName: String): AudioBuffer =
        fileFor(fileName).inputStream().buffered().use { WavReader.read(it) }

    fun readInfo(fileName: String): WavInfo {
        val file = fileFor(fileName)
        return file.inputStream().buffered().use { WavReader.readInfo(it, file.length()) }
    }

    fun write(fileName: String, buffer: AudioBuffer, depth: WavBitDepth = WavBitDepth.PCM_16) {
        // Write to a temporary file and rename. A crash midway then leaves the previous version
        // intact rather than a half-written file where the recording used to be.
        val target = fileFor(fileName)
        val temporary = File(target.parentFile, "${target.name}.writing")
        temporary.outputStream().buffered().use { WavWriter.write(buffer, it, depth) }
        if (!temporary.renameTo(target)) {
            temporary.copyTo(target, overwrite = true)
            temporary.delete()
        }
    }

    fun delete(fileName: String): Boolean = fileFor(fileName).delete()

    fun sizeOf(fileName: String): Long = fileFor(fileName).length()

    /**
     * Repairs a WAV whose header was never finalised, which is what a recording killed by the
     * system leaves behind.
     *
     * The audio samples are all there — only the two length fields in the header are stale. This
     * rewrites them in place, turning an unopenable file back into a complete recording.
     *
     * @return the number of audio frames recovered, or null if there was nothing to recover.
     */
    fun repairIncomplete(fileName: String, channelCount: Int, bytesPerSample: Int): Long? {
        val file = fileFor(fileName)
        if (!file.isFile) return null
        val length = file.length()
        if (length <= WavWriter.HEADER_BYTES) {
            // Header only: no audio was ever captured, so there is nothing worth keeping.
            file.delete()
            return null
        }
        RandomAccessFile(file, "rw").use { handle ->
            val header = ByteArray(WavWriter.HEADER_BYTES)
            handle.readFully(header)
            val dataBytes = WavWriter.repairTruncated(header, length)
            handle.seek(0)
            handle.write(header)
            val bytesPerFrame = bytesPerSample * channelCount
            return if (bytesPerFrame > 0) dataBytes / bytesPerFrame else null
        }
    }

    /** Free space on the volume holding the recordings, in bytes. */
    fun availableBytes(): Long = try {
        val stat = StatFs(recordingsDirectory.absolutePath)
        stat.availableBlocksLong * stat.blockSizeLong
    } catch (error: IllegalArgumentException) {
        0L
    }

    /**
     * How long recording can continue with the space that is left.
     *
     * Shown live on the Record screen. Running out of space mid-lecture with no warning is one of
     * the few failures a recorder cannot recover from, so it is surfaced before it happens rather
     * than reported afterwards.
     */
    fun remainingRecordingSeconds(sampleRate: Int, channelCount: Int, bytesPerSample: Int): Long {
        val bytesPerSecond = sampleRate.toLong() * channelCount * bytesPerSample
        if (bytesPerSecond <= 0) return 0
        // Hold back a little so the device does not end up completely full.
        val usable = (availableBytes() - RESERVED_BYTES).coerceAtLeast(0)
        return usable / bytesPerSecond
    }

    /** Removes export files older than a day. They are copies; the originals are untouched. */
    fun pruneExports(nowMillis: Long) {
        val cutoff = nowMillis - EXPORT_RETENTION_MILLIS
        exportsDirectory.listFiles()?.forEach { file ->
            if (file.lastModified() < cutoff) file.delete()
        }
    }

    private companion object {
        const val RESERVED_BYTES = 64L * 1024 * 1024
        const val EXPORT_RETENTION_MILLIS = 24L * 60 * 60 * 1000
    }
}
