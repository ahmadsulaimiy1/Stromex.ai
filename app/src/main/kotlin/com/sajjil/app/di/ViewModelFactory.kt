package com.sajjil.app.di

import android.app.Application
import com.sajjil.app.SajjilApplication

/**
 * Manual DI: SAJJIL's dependency graph is small enough (two repositories)
 * that a Dagger/Hilt setup would add ceremony without real benefit yet.
 * Each screen builds its ViewModel with androidx.lifecycle's
 * `viewModelFactory { initializer { ... } }` DSL, reading dependencies
 * from [asSajjilApplication].
 */
fun Application.asSajjilApplication(): SajjilApplication = this as SajjilApplication
