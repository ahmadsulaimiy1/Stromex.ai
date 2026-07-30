package com.sajjil.app.audio

import android.Manifest
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import androidx.annotation.RequiresPermission
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * One-shot capture used by SAJJIL AI Acoustic Intelligence's pre-recording
 * "Room Check": grabs a few seconds of room tone / a spoken test phrase and
 * hands it back as normalized float samples for `AcousticAnalyzer`. This is
 * intentionally separate from [AudioRecordEngine] — no processing chain, no
 * file writing, just a short raw capture held in memory.
 */
object AcousticProbeRecorder {

    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    suspend fun capture(durationSeconds: Double = 3.0, sampleRate: Int = 48000): FloatArray = withContext(Dispatchers.IO) {
        val minBufferSize = AudioRecord.getMinBufferSize(
            sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
        ).let { if (it > 0) it else 4096 }

        val record = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            minBufferSize * 2,
        )

        val totalSamples = (sampleRate * durationSeconds).toInt()
        val output = FloatArray(totalSamples)
        val shortBuffer = ShortArray(minBufferSize / 2)

        try {
            record.startRecording()
            var written = 0
            while (written < totalSamples) {
                val toRead = minOf(shortBuffer.size, totalSamples - written)
                val read = record.read(shortBuffer, 0, toRead)
                if (read <= 0) break
                for (i in 0 until read) output[written + i] = shortBuffer[i] / 32768f
                written += read
            }
            if (written < totalSamples) output.copyOf(written) else output
        } finally {
            record.stop()
            record.release()
        }
    }
}
