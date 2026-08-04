package ai.sajjil.app.ui.quran

import ai.sajjil.app.Services
import ai.sajjil.app.data.QuranProjectEntity
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class QuranUiState(
    val projects: List<QuranProjectEntity> = emptyList(),
    val completedByProject: Map<Long, Int> = emptyMap(),
    val selectedProjectId: Long? = null,
)

class QuranViewModel(private val services: Services) : ViewModel() {

    private val dao = services.database.quran()
    private val selected = MutableStateFlow<Long?>(null)

    /**
     * Completed-ayah counts for every project.
     *
     * Computed from the takes rather than stored on the project, so it cannot fall out of step
     * with reality — a denormalised counter is exactly the kind of thing that ends up wrong after
     * a delete and then quietly misreports someone's progress through the Qur'an.
     */
    private val completed = dao.observeProjects().map { projects ->
        withContext(Dispatchers.IO) {
            projects.associate { project ->
                val takes = dao.takesForRange(project.id, Int.MIN_VALUE, Int.MAX_VALUE)
                project.id to takes.filter { it.isSelected }.sumOf { it.ayahTo - it.ayahFrom + 1 }
            }
        }
    }

    val state: StateFlow<QuranUiState> = combine(
        dao.observeProjects(),
        completed,
        selected,
    ) { projects, counts, selectedId ->
        QuranUiState(
            projects = projects,
            completedByProject = counts,
            selectedProjectId = selectedId,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), QuranUiState())

    fun selectProject(id: Long) {
        selected.value = id
    }

    fun createProject(
        name: String,
        kind: QuranProjectKind,
        number: Int?,
        totalAyah: Int,
    ) {
        viewModelScope.launch {
            val now = System.currentTimeMillis()
            withContext(Dispatchers.IO) {
                dao.insertProject(
                    QuranProjectEntity(
                        name = name,
                        kind = kind.name,
                        surahNumber = if (kind == QuranProjectKind.SURAH) number else null,
                        juzNumber = if (kind == QuranProjectKind.JUZ) number else null,
                        createdAt = now,
                        updatedAt = now,
                        totalAyah = totalAyah.coerceAtLeast(1),
                    )
                )
            }
        }
    }

    fun deleteProject(project: QuranProjectEntity) {
        viewModelScope.launch {
            withContext(Dispatchers.IO) { dao.deleteProject(project) }
        }
    }

    /** Records a take against an ayah range. Multiple takes per range are the point. */
    fun addTake(projectId: Long, recordingId: Long, ayahFrom: Int, ayahTo: Int) {
        viewModelScope.launch {
            withContext(Dispatchers.IO) {
                val existing = dao.takesForRange(projectId, ayahFrom, ayahTo)
                dao.insertTake(
                    ai.sajjil.app.data.QuranTakeEntity(
                        projectId = projectId,
                        recordingId = recordingId,
                        ayahFrom = ayahFrom,
                        ayahTo = ayahTo,
                        takeNumber = existing.size + 1,
                        // The first take for a range becomes the keeper automatically; someone
                        // who records once should not have to also mark it as chosen.
                        isSelected = existing.isEmpty(),
                        createdAt = System.currentTimeMillis(),
                    )
                )
            }
        }
    }

    fun selectTake(take: ai.sajjil.app.data.QuranTakeEntity) {
        viewModelScope.launch {
            withContext(Dispatchers.IO) { dao.selectTake(take) }
        }
    }

    class Factory(private val services: Services) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T =
            QuranViewModel(services) as T
    }
}
