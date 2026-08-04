package ai.sautiy.core.analysis

import ai.sautiy.core.TestSignals
import ai.sautiy.core.audio.AudioBuffer
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class WaveformPeaksTest {

    @Test
    fun `a bucket reports the true extremes of the frames it covers`() {
        val samples = FloatArray(1_024)
        samples[10] = 0.9f
        samples[20] = -0.7f
        samples[300] = 0.4f
        val buffer = AudioBuffer.mono(samples, 48_000)

        val level = PeakBuilder(framesPerBucket = 256).also { it.append(buffer) }.finish()

        assertEquals(4, level.bucketCount)
        assertEquals(0.9f, level.maxima[0], 1e-6f)
        assertEquals(-0.7f, level.minima[0], 1e-6f)
        assertEquals("A quiet bucket must not inherit a loud one's peak", 0f, level.maxima[2], 1e-6f)
        assertEquals(0.4f, level.maxima[1], 1e-6f)
    }

    @Test
    fun `asymmetric material is drawn asymmetrically`() {
        // Speech is asymmetric. A waveform built from magnitude alone would draw this as a
        // symmetric shape and hide the DC-offset and plosive behaviour a user needs to see.
        val samples = FloatArray(256) { 0.8f }
        samples[0] = -0.1f
        val level = PeakBuilder(256).also { it.append(AudioBuffer.mono(samples, 48_000)) }.finish()

        assertEquals(0.8f, level.maxima[0], 1e-6f)
        assertEquals(-0.1f, level.minima[0], 1e-6f)
        assertTrue(
            "The envelope must not be forced symmetric",
            kotlin.math.abs(level.maxima[0]) != kotlin.math.abs(level.minima[0]),
        )
    }

    @Test
    fun `rms tracks energy rather than extremes`() {
        val steady = AudioBuffer.mono(FloatArray(256) { 0.5f }, 48_000)
        val spiky = FloatArray(256).also { it[0] = 1.0f }

        val steadyLevel = PeakBuilder(256).also { it.append(steady) }.finish()
        val spikyLevel = PeakBuilder(256).also { it.append(AudioBuffer.mono(spiky, 48_000)) }.finish()

        assertEquals(0.5, steadyLevel.rms[0].toDouble(), 1e-4)
        assertTrue(
            "A single spike must not read as loud in RMS",
            spikyLevel.rms[0] < 0.07f,
        )
        assertEquals("...but its peak must still be visible", 1.0f, spikyLevel.maxima[0], 1e-6f)
    }

    @Test
    fun `decimation preserves extremes exactly`() {
        // A zoomed-out waveform that loses a transient is worse than useless: it tells the user
        // there is no click at the very moment they are hunting for one.
        val buffer = TestSignals.noise(0.5, 48_000, amplitude = 0.3).also {
            it.channels[0][12_345] = 0.99f
        }
        val base = PeakBuilder(256).also { it.append(buffer) }.finish()
        val coarse = base.decimate(4).decimate(4)

        assertEquals(
            "The loudest sample vanished when zooming out",
            base.maxima.max(),
            coarse.maxima.max(),
            1e-6f,
        )
        assertEquals(base.minima.min(), coarse.minima.min(), 1e-6f)
    }

    @Test
    fun `the pyramid spans from fine detail to a whole recording`() {
        val buffer = TestSignals.noise(10.0, 48_000)
        val pyramid = Waveform.pyramid(buffer)

        assertEquals(Waveform.PYRAMID_LEVELS, pyramid.levels.size)
        assertEquals(256, pyramid.levels.first().framesPerBucket)
        assertEquals(256 * 4 * 4 * 4 * 4, pyramid.levels.last().framesPerBucket)
        assertTrue(
            "Each level must be coarser than the one below it",
            pyramid.levels.zipWithNext().all { it.first.framesPerBucket < it.second.framesPerBucket },
        )
    }

    @Test
    fun `the pyramid picks a level that never reads more buckets than there are pixels`() {
        val buffer = TestSignals.noise(60.0, 48_000)
        val pyramid = Waveform.pyramid(buffer)

        // Whole recording on a 1080-pixel-wide display.
        val wide = pyramid.levelFor(frameSpan = 60L * 48_000, pixelWidth = 1_080)
        assertTrue(
            "Drawing an hour-scale view from fine buckets would cost thousands of reads per column",
            wide.framesPerBucket >= (60L * 48_000 / 1_080) / 4,
        )

        // Fully zoomed in on 40 ms.
        val tight = pyramid.levelFor(frameSpan = 1_920, pixelWidth = 1_080)
        assertEquals("Maximum zoom must use the finest level", pyramid.base.framesPerBucket, tight.framesPerBucket)
    }

    @Test
    fun `columns returns exactly one entry per pixel`() {
        val buffer = TestSignals.sine(200.0, 5.0, 48_000, amplitude = 0.8)
        val pyramid = Waveform.pyramid(buffer)

        for (width in listOf(1, 7, 320, 1_080, 1_440)) {
            val columns = pyramid.columns(0, buffer.frameCount.toLong(), width)
            assertEquals(width, columns.width)
            assertEquals(width, columns.minima.size)
            assertEquals(width, columns.rms.size)
        }
    }

    @Test
    fun `columns beyond the end of the audio are silent rather than an error`() {
        // While recording, the view legitimately runs ahead of the material.
        val buffer = TestSignals.sine(440.0, 1.0, 48_000, amplitude = 0.8)
        val pyramid = Waveform.pyramid(buffer)

        val columns = pyramid.columns(0, 3L * 48_000, 300)
        assertEquals(300, columns.width)
        assertTrue("Real audio must still be drawn", columns.maxima.take(90).max() > 0.5f)
        assertEquals("Beyond the end must be silence", 0f, columns.maxima.last(), 1e-6f)
    }

    @Test
    fun `a full recording view still shows the loudest moment`() {
        val buffer = TestSignals.noise(30.0, 48_000, amplitude = 0.2)
        buffer.channels[0][1_000_000] = 0.95f
        val pyramid = Waveform.pyramid(buffer)

        val columns = pyramid.columns(0, buffer.frameCount.toLong(), 1_080)
        assertTrue(
            "The peak of the recording disappeared at full zoom-out: ${columns.maxima.max()}",
            columns.maxima.max() > 0.9f,
        )
    }

    @Test
    fun `incremental building matches building all at once`() {
        // The live waveform is built block by block while recording; opening the finished file
        // builds it in one pass. They must agree, or the waveform visibly changes on save.
        val whole = TestSignals.noise(1.0, 48_000, amplitude = 0.4)

        val atOnce = PeakBuilder(256).also { it.append(whole) }.finish()

        val incremental = PeakBuilder(256)
        var offset = 0
        val blockSizes = listOf(1_000, 4_800, 137, 9_600, 512)
        var i = 0
        while (offset < whole.frameCount) {
            val size = minOf(blockSizes[i % blockSizes.size], whole.frameCount - offset)
            incremental.append(whole.slice(offset, offset + size))
            offset += size
            i++
        }
        val built = incremental.finish()

        assertEquals(atOnce.bucketCount, built.bucketCount)
        for (b in 0 until atOnce.bucketCount) {
            assertEquals("bucket $b max", atOnce.maxima[b], built.maxima[b], 1e-6f)
            assertEquals("bucket $b min", atOnce.minima[b], built.minima[b], 1e-6f)
            assertEquals("bucket $b rms", atOnce.rms[b], built.rms[b], 1e-5f)
        }
    }

    @Test
    fun `a snapshot mid-recording includes the bucket still being filled`() {
        val builder = PeakBuilder(256)
        builder.append(AudioBuffer.mono(FloatArray(100) { 0.6f }, 48_000))

        val snapshot = builder.snapshot()
        assertEquals("The in-progress bucket must be visible immediately", 1, snapshot.bucketCount)
        assertEquals(0.6f, snapshot.maxima[0], 1e-6f)

        // Snapshotting must not disturb the builder.
        builder.append(AudioBuffer.mono(FloatArray(156) { 0.6f }, 48_000))
        assertEquals(1, builder.finish().bucketCount)
    }

    @Test
    fun `the meter reports peak and rms separately and flags real clipping`() {
        val sine = TestSignals.sine(1_000.0, 0.1, 48_000, amplitude = 0.5)
        val level = Waveform.instantLevel(sine)

        assertEquals(-6.02, level.peakDb, 0.1)
        assertEquals("RMS of a sine sits 3 dB below its peak", -9.03, level.rmsDb, 0.1)
        assertTrue(!level.isClipping)

        val hot = AudioBuffer.mono(floatArrayOf(0.1f, 1.0f, 0.1f), 48_000)
        assertTrue("Full-scale material must be reported as clipping", Waveform.instantLevel(hot).isClipping)
    }

    @Test
    fun `silence reads as the floor, not as an error`() {
        val level = Waveform.instantLevel(TestSignals.silence(0.1, 48_000))
        assertEquals(ai.sautiy.core.audio.Decibels.FLOOR_DB, level.peakDb, 0.0)
        assertTrue(level.peakDb.isFinite())
    }
}
