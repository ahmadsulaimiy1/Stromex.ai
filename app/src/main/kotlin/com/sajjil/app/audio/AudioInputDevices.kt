package com.sajjil.app.audio

import android.content.Context
import android.media.AudioDeviceInfo
import android.media.AudioManager

/**
 * SAJJIL USB Professional Microphone Support: Android exposes USB audio
 * class devices (RØDE, Shure, Audio-Technica, DJI, Hollyland, BOYA, Maono,
 * etc. all speak standard USB Audio Class over USB-C/OTG) through
 * [AudioManager]'s device list — no vendor SDK needed. This lists the
 * relevant input devices so the user can pick one; [AudioRecordEngine]
 * then calls `AudioRecord.setPreferredDevice` with the selection.
 *
 * "Automatic microphone profiling" (recognizing *which specific model* is
 * connected and loading a measured correction curve for it) needs a
 * database of measured device product/vendor IDs SAJJIL doesn't have yet —
 * see `MicrophoneProfile` for the honest, character-based alternative
 * shipped today.
 */
object AudioInputDevices {

    fun list(context: Context): List<AudioDeviceInfo> {
        val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        return audioManager.getDevices(AudioManager.GET_DEVICES_INPUTS)
            .filter { it.type in relevantTypes }
            .sortedByDescending { it.type == AudioDeviceInfo.TYPE_USB_DEVICE || it.type == AudioDeviceInfo.TYPE_USB_HEADSET }
    }

    fun friendlyName(device: AudioDeviceInfo): String = when (device.type) {
        AudioDeviceInfo.TYPE_USB_DEVICE, AudioDeviceInfo.TYPE_USB_HEADSET, AudioDeviceInfo.TYPE_USB_ACCESSORY ->
            "${device.productName} (USB)"
        AudioDeviceInfo.TYPE_WIRED_HEADSET -> "${device.productName} (Wired)"
        AudioDeviceInfo.TYPE_BLUETOOTH_SCO -> "${device.productName} (Bluetooth)"
        AudioDeviceInfo.TYPE_BUILTIN_MIC -> "Built-in Microphone"
        else -> device.productName?.toString() ?: "Unknown Input"
    }

    private val relevantTypes = setOf(
        AudioDeviceInfo.TYPE_BUILTIN_MIC,
        AudioDeviceInfo.TYPE_USB_DEVICE,
        AudioDeviceInfo.TYPE_USB_HEADSET,
        AudioDeviceInfo.TYPE_USB_ACCESSORY,
        AudioDeviceInfo.TYPE_WIRED_HEADSET,
        AudioDeviceInfo.TYPE_BLUETOOTH_SCO,
    )
}
