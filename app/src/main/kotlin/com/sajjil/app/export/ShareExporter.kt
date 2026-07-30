package com.sajjil.app.export

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

/**
 * Builds a share [Intent] for a recording file via [FileProvider] -- generic, so whatever the
 * user's share sheet offers (WhatsApp, Telegram, Drive, Dropbox, email, ...) works without
 * SAJJIL needing per-app integration code. Android has blocked raw file:// URIs across app
 * boundaries since API 24, hence the FileProvider indirection rather than a plain Uri.fromFile.
 */
object ShareExporter {
    fun shareIntent(context: Context, file: File): Intent {
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
        val send = Intent(Intent.ACTION_SEND).apply {
            type = mimeTypeFor(file)
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        return Intent.createChooser(send, "Share recording")
    }

    fun mimeTypeFor(file: File): String = when (file.extension.lowercase()) {
        "wav" -> "audio/wav"
        "m4a" -> "audio/mp4"
        else -> "audio/*"
    }
}
