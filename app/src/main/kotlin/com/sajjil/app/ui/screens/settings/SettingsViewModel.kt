package com.sajjil.app.ui.screens.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sajjil.app.di.asSajjilApplication
import com.sajjil.app.ui.theme.SajjilTheme
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class SettingsViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application.asSajjilApplication()

    val theme: StateFlow<SajjilTheme> = app.settingsRepository.theme
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), SajjilTheme.ROYAL_NAVY_DEEP)

    fun setTheme(theme: SajjilTheme) {
        viewModelScope.launch { app.settingsRepository.setTheme(theme) }
    }
}
