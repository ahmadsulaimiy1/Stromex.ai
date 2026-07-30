package com.sajjil.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.app.navigation.SajjilNavGraph
import com.sajjil.app.ui.theme.SajjilAppTheme

class MainActivity : ComponentActivity() {

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            microphoneGranted = granted
        }

    private var microphoneGranted by mutableStateOf(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        microphoneGranted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.RECORD_AUDIO,
        ) == PackageManager.PERMISSION_GRANTED
        if (!microphoneGranted) {
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }

        val app = application.asSajjilApplication()

        setContent {
            val theme by app.settingsRepository.theme.collectAsStateWithLifecycle(
                initialValue = com.sajjil.app.ui.theme.SajjilTheme.ROYAL_NAVY_DEEP,
            )
            SajjilAppTheme(theme = theme) {
                SajjilNavGraph(
                    application = app,
                    microphoneGranted = microphoneGranted,
                    onRequestMicrophone = { permissionLauncher.launch(Manifest.permission.RECORD_AUDIO) },
                )
            }
        }
    }
}
