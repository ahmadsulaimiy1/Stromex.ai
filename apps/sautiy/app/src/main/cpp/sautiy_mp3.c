/*
 * SAUTIY MP3 encoder bridge — JNI over LAME.
 *
 * Android has no MP3 encoder. This is the thin, boring layer between Mp3Encoder.kt and
 * libmp3lame; all of the actual encoding is LAME's.
 *
 * Deliberately small: it holds no state of its own beyond the LAME handle, does no buffering,
 * and copies once in each direction. Anything cleverer here would be optimising a path that is
 * already bounded by LAME's own work.
 */
#include <jni.h>
#include <stdlib.h>
/* intptr_t, used to round-trip the LAME handle through a jlong. */
#include <stdint.h>
/* lame/include is on the include path, so the header is <lame.h> and not <lame/lame.h>. */
#include <lame.h>

#define SAUTIY_JNI(name) Java_ai_sautiy_export_Mp3Encoder_##name

JNIEXPORT jlong JNICALL SAUTIY_JNI(nativeInit)(
        JNIEnv *env, jobject self, jint sampleRate, jint channels, jint bitrateKbps) {
    (void) env; (void) self;

    lame_global_flags *lame = lame_init();
    if (lame == NULL) return 0;

    lame_set_in_samplerate(lame, sampleRate);
    lame_set_out_samplerate(lame, sampleRate);
    lame_set_num_channels(lame, channels);
    lame_set_mode(lame, channels == 1 ? MONO : JOINT_STEREO);
    lame_set_brate(lame, bitrateKbps);

    /* Quality 2 is LAME's near-best setting; 0 costs several times the CPU for a difference
     * nobody has reliably heard, and this runs on a phone battery. */
    lame_set_quality(lame, 2);

    /* SAUTIY writes its own ID3 tag before the first frame, because LAME's tag writer wants a
     * seekable file and exports go into a document URI that may not be seekable. */
    lame_set_write_id3tag_automatic(lame, 0);

    if (lame_init_params(lame) < 0) {
        lame_close(lame);
        return 0;
    }
    return (jlong) (intptr_t) lame;
}

JNIEXPORT jint JNICALL SAUTIY_JNI(nativeEncode)(
        JNIEnv *env, jobject self, jlong handle, jbyteArray pcm, jint offset, jint frames,
        jbyteArray out) {
    (void) self;
    lame_global_flags *lame = (lame_global_flags *) (intptr_t) handle;
    if (lame == NULL) return -1;

    jbyte *pcmBytes = (*env)->GetPrimitiveArrayCritical(env, pcm, NULL);
    jbyte *outBytes = (*env)->GetPrimitiveArrayCritical(env, out, NULL);
    if (pcmBytes == NULL || outBytes == NULL) {
        if (pcmBytes) (*env)->ReleasePrimitiveArrayCritical(env, pcm, pcmBytes, JNI_ABORT);
        if (outBytes) (*env)->ReleasePrimitiveArrayCritical(env, out, outBytes, JNI_ABORT);
        return -2;
    }

    short *samples = (short *) (pcmBytes + offset);
    const jsize outCapacity = (*env)->GetArrayLength(env, out);
    const int channels = lame_get_num_channels(lame);

    /* Refuse a read that would run off the end of the array rather than performing it.
     * Without this a wrong frame count is a native segfault that takes the whole process with
     * it, and the Java side sees no exception, no message and no stack — just a dead app. */
    const jsize pcmLength = (*env)->GetArrayLength(env, pcm);
    const long needed = (long) offset + (long) frames * channels * 2L;
    if (offset < 0 || frames < 0 || needed > (long) pcmLength) {
        (*env)->ReleasePrimitiveArrayCritical(env, pcm, pcmBytes, JNI_ABORT);
        (*env)->ReleasePrimitiveArrayCritical(env, out, outBytes, JNI_ABORT);
        return -3;
    }

    int written;
    if (channels == 1) {
        /* lame_encode_buffer_interleaved is documented for stereo and reads two samples per
         * frame regardless of the configured channel count. Handing it mono audio makes it read
         * twice the data that is there — an overrun that crashes the process rather than
         * returning an error. Mono goes through the separate-channel entry point, which reads
         * only the left buffer when the encoder is mono. */
        written = lame_encode_buffer(
                lame, samples, samples, frames, (unsigned char *) outBytes, outCapacity);
    } else {
        written = lame_encode_buffer_interleaved(
                lame, samples, frames, (unsigned char *) outBytes, outCapacity);
    }

    (*env)->ReleasePrimitiveArrayCritical(env, pcm, pcmBytes, JNI_ABORT);
    (*env)->ReleasePrimitiveArrayCritical(env, out, outBytes, 0);
    return written;
}

JNIEXPORT jint JNICALL SAUTIY_JNI(nativeFlush)(
        JNIEnv *env, jobject self, jlong handle, jbyteArray out) {
    (void) self;
    lame_global_flags *lame = (lame_global_flags *) (intptr_t) handle;
    if (lame == NULL) return -1;

    jbyte *outBytes = (*env)->GetPrimitiveArrayCritical(env, out, NULL);
    if (outBytes == NULL) return -2;

    const jsize outCapacity = (*env)->GetArrayLength(env, out);
    int written = lame_encode_flush(lame, (unsigned char *) outBytes, outCapacity);

    (*env)->ReleasePrimitiveArrayCritical(env, out, outBytes, 0);
    return written;
}

JNIEXPORT void JNICALL SAUTIY_JNI(nativeClose)(JNIEnv *env, jobject self, jlong handle) {
    (void) env; (void) self;
    lame_global_flags *lame = (lame_global_flags *) (intptr_t) handle;
    if (lame != NULL) lame_close(lame);
}
