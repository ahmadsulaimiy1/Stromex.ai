package com.sajjil.app.navigation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Analytics
import androidx.compose.material.icons.filled.Assistant
import androidx.compose.material.icons.filled.CompareArrows
import androidx.compose.material.icons.filled.FactCheck
import androidx.compose.material.icons.filled.RecordVoiceOver
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import androidx.navigation.NavType
import com.sajjil.app.SajjilApplication
import com.sajjil.app.ui.screens.analytics.AnalyticsScreen
import com.sajjil.app.ui.screens.analytics.AnalyticsViewModel
import com.sajjil.app.ui.screens.archive.ArchiveScreen
import com.sajjil.app.ui.screens.archive.ArchiveViewModel
import com.sajjil.app.ui.screens.assistant.AssistantScreen
import com.sajjil.app.ui.screens.assistant.AssistantViewModel
import com.sajjil.app.ui.screens.batch.BatchProductionScreen
import com.sajjil.app.ui.screens.batch.BatchProductionViewModel
import com.sajjil.app.ui.screens.comparison.ComparisonLabScreen
import com.sajjil.app.ui.screens.comparison.ComparisonLabViewModel
import com.sajjil.app.ui.screens.dashboard.DashboardScreen
import com.sajjil.app.ui.screens.dashboard.DashboardViewModel
import com.sajjil.app.ui.screens.enhance.EnhanceScreen
import com.sajjil.app.ui.screens.enhance.EnhanceViewModel
import com.sajjil.app.ui.screens.master.MasterScreen
import com.sajjil.app.ui.screens.master.MasterViewModel
import com.sajjil.app.ui.screens.quranproject.QuranProjectScreen
import com.sajjil.app.ui.screens.quranproject.QuranProjectViewModel
import com.sajjil.app.ui.screens.quranstudio.QuranStudioScreen
import com.sajjil.app.ui.screens.quranstudio.QuranStudioViewModel
import com.sajjil.app.ui.screens.readiness.ProductionReadinessScreen
import com.sajjil.app.ui.screens.readiness.ProductionReadinessViewModel
import com.sajjil.app.ui.screens.record.RecordScreen
import com.sajjil.app.ui.screens.record.RecordViewModel
import com.sajjil.app.ui.screens.settings.SettingsScreen
import com.sajjil.app.ui.screens.settings.SettingsViewModel
import com.sajjil.app.ui.screens.speechsettings.SpeechCapabilityScreen
import com.sajjil.app.ui.screens.speechsettings.SpeechCapabilityViewModel
import com.sajjil.app.ui.screens.voicestudio.VoiceStudioScreen
import com.sajjil.app.ui.screens.voicestudio.VoiceStudioViewModel

@Composable
fun SajjilNavGraph(
    application: SajjilApplication,
    microphoneGranted: Boolean,
    onRequestMicrophone: () -> Unit,
) {
    val navController = rememberNavController()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("SAJJIL") },
                actions = {
                    IconButton(onClick = { navController.navigate(SajjilRoutes.ASSISTANT) }) {
                        Icon(Icons.Filled.Assistant, contentDescription = "SAJJIL Assistant")
                    }
                    IconButton(onClick = { navController.navigate(SajjilRoutes.PRODUCTION_READINESS) }) {
                        Icon(Icons.Filled.FactCheck, contentDescription = "Production Readiness")
                    }
                    IconButton(onClick = { navController.navigate(SajjilRoutes.VOICE_STUDIO) }) {
                        Icon(Icons.Filled.RecordVoiceOver, contentDescription = "Voice Studio")
                    }
                    IconButton(onClick = { navController.navigate(SajjilRoutes.ANALYTICS) }) {
                        Icon(Icons.Filled.Analytics, contentDescription = "Executive Analytics")
                    }
                    IconButton(onClick = { navController.navigate(SajjilRoutes.COMPARISON_LAB) }) {
                        Icon(Icons.Filled.CompareArrows, contentDescription = "Comparison Lab")
                    }
                    IconButton(onClick = { navController.navigate(SajjilRoutes.SETTINGS) }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings")
                    }
                },
            )
        },
        bottomBar = {
            val backStackEntry by navController.currentBackStackEntryAsState()
            val currentDestination = backStackEntry?.destination
            NavigationBar {
                SajjilDestination.bottomNavItems.forEach { destination ->
                    NavigationBarItem(
                        selected = currentDestination?.hierarchy?.any { it.route == destination.route } == true,
                        onClick = {
                            navController.navigate(destination.route) {
                                popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(destination.icon, contentDescription = destination.label) },
                        label = { Text(destination.label) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = SajjilDestination.Record.route,
            modifier = Modifier.fillMaxSize().padding(padding),
        ) {
            composable(SajjilDestination.Record.route) {
                if (microphoneGranted) {
                    val viewModel: RecordViewModel = viewModel(factory = viewModelFactory {
                        initializer { RecordViewModel(application) }
                    })
                    RecordScreen(viewModel)
                } else {
                    MicrophonePermissionPrompt(onRequestMicrophone)
                }
            }
            composable(SajjilDestination.Enhance.route) {
                val viewModel: EnhanceViewModel = viewModel(factory = viewModelFactory {
                    initializer { EnhanceViewModel(application) }
                })
                EnhanceScreen(viewModel)
            }
            composable(SajjilDestination.Master.route) {
                val viewModel: MasterViewModel = viewModel(factory = viewModelFactory {
                    initializer { MasterViewModel(application) }
                })
                MasterScreen(viewModel)
            }
            composable(SajjilDestination.Archive.route) {
                val viewModel: ArchiveViewModel = viewModel(factory = viewModelFactory {
                    initializer { ArchiveViewModel(application) }
                })
                ArchiveScreen(viewModel, onOpenDashboard = { id -> navController.navigate(SajjilRoutes.dashboard(id)) })
            }
            composable(SajjilDestination.QuranStudio.route) {
                val viewModel: QuranStudioViewModel = viewModel(factory = viewModelFactory {
                    initializer { QuranStudioViewModel(application) }
                })
                QuranStudioScreen(
                    viewModel,
                    onOpenBatchProduction = { navController.navigate(SajjilRoutes.BATCH_PRODUCTION) },
                    onOpenSurahProject = { surahNumber -> navController.navigate(SajjilRoutes.quranProject(surahNumber)) },
                )
            }
            composable(
                route = SajjilRoutes.QURAN_PROJECT,
                arguments = listOf(navArgument("surahNumber") { type = NavType.IntType }),
            ) { backStackEntry ->
                val surahNumber = backStackEntry.arguments?.getInt("surahNumber") ?: return@composable
                val viewModel: QuranProjectViewModel = viewModel(factory = viewModelFactory {
                    initializer { QuranProjectViewModel(application) }
                })
                QuranProjectScreen(viewModel, surahNumber)
            }
            composable(SajjilRoutes.BATCH_PRODUCTION) {
                val viewModel: BatchProductionViewModel = viewModel(factory = viewModelFactory {
                    initializer { BatchProductionViewModel(application) }
                })
                BatchProductionScreen(viewModel)
            }
            composable(SajjilRoutes.ANALYTICS) {
                val viewModel: AnalyticsViewModel = viewModel(factory = viewModelFactory {
                    initializer { AnalyticsViewModel(application) }
                })
                AnalyticsScreen(viewModel)
            }
            composable(SajjilRoutes.COMPARISON_LAB) {
                val viewModel: ComparisonLabViewModel = viewModel(factory = viewModelFactory {
                    initializer { ComparisonLabViewModel(application) }
                })
                ComparisonLabScreen(viewModel)
            }
            composable(SajjilRoutes.ASSISTANT) {
                val viewModel: AssistantViewModel = viewModel(factory = viewModelFactory {
                    initializer { AssistantViewModel(application) }
                })
                AssistantScreen(viewModel)
            }
            composable(SajjilRoutes.PRODUCTION_READINESS) {
                val viewModel: ProductionReadinessViewModel = viewModel(factory = viewModelFactory {
                    initializer { ProductionReadinessViewModel(application) }
                })
                ProductionReadinessScreen(viewModel)
            }
            composable(SajjilRoutes.VOICE_STUDIO) {
                if (microphoneGranted) {
                    val viewModel: VoiceStudioViewModel = viewModel(factory = viewModelFactory {
                        initializer { VoiceStudioViewModel(application) }
                    })
                    VoiceStudioScreen(viewModel)
                } else {
                    MicrophonePermissionPrompt(onRequestMicrophone)
                }
            }
            composable(SajjilRoutes.SPEECH_CAPABILITY) {
                val viewModel: SpeechCapabilityViewModel = viewModel(factory = viewModelFactory {
                    initializer { SpeechCapabilityViewModel(application) }
                })
                SpeechCapabilityScreen(viewModel)
            }
            composable(SajjilRoutes.SETTINGS) {
                val viewModel: SettingsViewModel = viewModel(factory = viewModelFactory {
                    initializer { SettingsViewModel(application) }
                })
                SettingsScreen(viewModel, onOpenSpeechCapability = { navController.navigate(SajjilRoutes.SPEECH_CAPABILITY) })
            }
            composable(
                route = SajjilRoutes.DASHBOARD,
                arguments = listOf(navArgument("recordingId") { type = NavType.LongType }),
            ) { backStackEntry ->
                val recordingId = backStackEntry.arguments?.getLong("recordingId") ?: return@composable
                val viewModel: DashboardViewModel = viewModel(factory = viewModelFactory {
                    initializer { DashboardViewModel(application) }
                })
                DashboardScreen(viewModel, recordingId)
            }
        }
    }
}

@Composable
private fun MicrophonePermissionPrompt(onRequestMicrophone: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text("SAJJIL needs microphone access to record.")
        androidx.compose.material3.Button(onClick = onRequestMicrophone) { Text("Grant Microphone Access") }
    }
}
