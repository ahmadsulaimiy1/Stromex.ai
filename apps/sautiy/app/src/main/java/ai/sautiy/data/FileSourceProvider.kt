package ai.sautiy.data

import ai.sautiy.core.audio.AudioBuffer
import ai.sautiy.core.codec.WavCodec
import ai.sautiy.core.edit.SourceProvider
import java.io.File

/**
 * Reads source audio from the take files on disk — Editorial Bible chapter 16.2 and 16.3.
 *
 * This exists instead of holding captured audio in memory, and the difference is not an
 * optimisation. A ninety-minute lecture at 48 kHz is about 500 MB as 32-bit float; keeping it
 * in the heap would breach the constitutional in-memory ceiling four times over, and would do
 * it on exactly the recording that matters most to the person making it.
 *
 * Reading ranges instead means a two-hour project opens as fast as a two-minute one, playback
 * starts on the block it is about to play, and the editor never loads what it is not showing.
 *
 * A small LRU of recently read blocks absorbs the overlap between consecutive playback windows
 * and the repeated reads of a scrub, without which the same frames would be decoded several
 * times a second.
 */
class FileSourceProvider(
    private val files: SautiyFiles,
    private val cacheBlocks: Int = DEFAULT_CACHE_BLOCKS,
) : SourceProvider {

    private data class Key(val sourceId: String, val startFrame: Long, val frameCount: Int)

    private val cache = object : LinkedHashMap<Key, AudioBuffer>(16, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<Key, AudioBuffer>?): Boolean =
            size > cacheBlocks
    }

    override fun read(sourceId: String, startFrame: Long, frameCount: Int): AudioBuffer {
        if (frameCount <= 0) return AudioBuffer.silence(1, 0, 48_000)

        val key = Key(sourceId, startFrame, frameCount)
        synchronized(cache) { cache[key] }?.let { return it }

        val file: File = files.takeFile(sourceId)
        if (!file.isFile) return AudioBuffer.silence(1, frameCount, 48_000)

        val read = runCatching { WavCodec.readRange(file, startFrame, frameCount.toLong()) }
            .getOrElse { return AudioBuffer.silence(1, frameCount, 48_000) }

        // A read past the end of a source is padded rather than short, so the renderer's
        // arithmetic never has to special-case the tail of a take.
        val block = if (read.frameCount == frameCount) {
            read
        } else {
            AudioBuffer.silence(read.channelCount.coerceAtLeast(1), frameCount, read.sampleRate).also { padded ->
                for (c in 0 until read.channelCount) {
                    read.channels[c].copyInto(padded.channels[c], 0)
                }
            }
        }

        synchronized(cache) { cache[key] = block }
        return block
    }

    fun clear() {
        synchronized(cache) { cache.clear() }
    }

    private companion object {
        /**
         * Sixteen blocks. At the playback window size that is under a second of audio held —
         * enough to absorb window overlap and scrubbing, far too little to matter against the
         * chapter 16.3 ceiling.
         */
        const val DEFAULT_CACHE_BLOCKS = 16
    }
}
