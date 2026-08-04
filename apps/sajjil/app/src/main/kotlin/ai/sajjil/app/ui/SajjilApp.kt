package ai.sajjil.app.ui

import ai.sajjil.app.Services
import ai.sajjil.app.ui.assistant.AssistantScreen
import ai.sajjil.app.ui.library.LibraryScreen
import ai.sajjil.app.ui.quran.QuranScreen
import ai.sajjil.app.ui.record.RecordScreen
import ai.sajjil.app.ui.studio.StudioScreen
import ai.sajjil.app.ui.theme.sajjilColors
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.FiberManualRecord
import androidx.compose.material.icons.filled.LibraryMusic
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

/**
 * The five sections.
 *
 * Five and no more, and no nesting beneath them beyond a detail view. A recorder that grows a
 * sixth tab has stopped being a recorder; anything that would want one belongs inside one of
 * these instead.
 */
enum class Section(
    val route: String,
    val label: String,
    val icon: ImageVector,
) {
    RECORD("record", "Record", Icons.Filled.FiberManualRecord),
    STUDIO("studio", "Studio", Icons.Filled.Tune),
    LIBRARY("library", "Library", Icons.Filled.LibraryMusic),
    QURAN("quran", "Qur'an", Icons.Filled.MenuBook),
    ASSISTANT("assistant", "Assistant", Icons.Filled.AutoAwesome),
}

@Composable
fun SajjilApp(services: Services) {
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = backStackEntry?.destination

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        bottomBar = {
            NavigationBar(
                containerColor = sajjilColors.surfaceElevated,
                tonalElevation = 0.dp,
            ) {
                for (section in Section.entries) {
                    val selected = currentDestination?.hierarchy?.any { it.route == section.route } == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            navController.navigate(section.route) {
                                // Switching sections returns to that section's root rather than
                                // stacking screens forever, and re-selecting the current tab is a
                                // no-op instead of pushing a duplicate.
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(section.icon, contentDescription = null) },
                        label = { Text(section.label) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = MaterialTheme.colorScheme.primary,
                            selectedTextColor = MaterialTheme.colorScheme.primary,
                            indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.12f),
                            unselectedIconColor = sajjilColors.onSurfaceMuted,
                            unselectedTextColor = sajjilColors.onSurfaceMuted,
                        ),
                    )
                }
            }
        },
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            NavHost(
                navController = navController,
                startDestination = Section.RECORD.route,
            ) {
                composable(Section.RECORD.route) {
                    RecordScreen(
                        services = services,
                        onOpenInStudio = { recordingId ->
                            navController.navigateToStudio(recordingId)
                        },
                        onOpenLibrary = { navController.navigate(Section.LIBRARY.route) },
                    )
                }
                composable(Section.STUDIO.route) {
                    StudioScreen(
                        services = services,
                        recordingId = null,
                        onOpenLibrary = { navController.navigate(Section.LIBRARY.route) },
                        onStartRecording = { navController.navigate(Section.RECORD.route) },
                    )
                }
                composable(
                    route = "${Section.STUDIO.route}/{recordingId}",
                    arguments = listOf(
                        androidx.navigation.navArgument("recordingId") {
                            type = androidx.navigation.NavType.LongType
                        }
                    ),
                ) { entry ->
                    StudioScreen(
                        services = services,
                        recordingId = entry.arguments?.getLong("recordingId"),
                        onOpenLibrary = { navController.navigate(Section.LIBRARY.route) },
                        onStartRecording = { navController.navigate(Section.RECORD.route) },
                    )
                }
                composable(Section.LIBRARY.route) {
                    LibraryScreen(
                        services = services,
                        onOpen = { recordingId -> navController.navigateToStudio(recordingId) },
                        onStartRecording = { navController.navigate(Section.RECORD.route) },
                    )
                }
                composable(Section.QURAN.route) {
                    QuranScreen(
                        services = services,
                        onOpenRecording = { recordingId -> navController.navigateToStudio(recordingId) },
                        onStartRecording = { navController.navigate(Section.RECORD.route) },
                    )
                }
                composable(Section.ASSISTANT.route) {
                    AssistantScreen(services = services)
                }
            }
        }
    }
}

private fun androidx.navigation.NavHostController.navigateToStudio(recordingId: Long) {
    navigate("${Section.STUDIO.route}/$recordingId") {
        launchSingleTop = true
    }
}
