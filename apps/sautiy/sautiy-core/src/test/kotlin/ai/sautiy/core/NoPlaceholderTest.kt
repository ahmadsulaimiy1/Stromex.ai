package ai.sautiy.core

import java.io.File
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Editorial Bible chapter 1.10 — the no-placeholder clause — enforced by the build.
 *
 * The banned tokens are assembled at runtime rather than written literally, so that this file
 * can enforce the rule without violating it.
 */
class NoPlaceholderTest {

    private val bannedTokens: List<String> = listOf(
        "TO" + "DO",
        "FIX" + "ME",
        "Place" + "holder",
        "Coming " + "Soon",
        "Future " + "Work",
        "Not " + "Implemented",
        "XX" + "X",
        "stub" + "bed out",
        "unimplemented" + "()",
    )

    /** This file legitimately contains the banned words; nothing else may. */
    private val exemptFileNames = setOf("NoPlaceholderTest.kt")

    private fun sourceRoot(): File {
        // Gradle runs tests with the module directory as the working directory.
        val moduleDir = File(".").canonicalFile
        val sautiyRoot = moduleDir.parentFile
        return sautiyRoot ?: error("Unable to locate the SAUTIY source root from $moduleDir")
    }

    private fun scannableFiles(): List<File> =
        sourceRoot().walkTopDown()
            .onEnter { dir -> dir.name !in setOf("build", ".gradle", ".idea", "generated") }
            .filter { it.isFile }
            .filter { it.extension in setOf("kt", "kts", "xml") }
            .filter { it.name !in exemptFileNames }
            .toList()

    @Test
    fun `the source tree contains no placeholder tokens`() {
        val violations = mutableListOf<String>()

        for (file in scannableFiles()) {
            file.readLines().forEachIndexed { index, line ->
                for (token in bannedTokens) {
                    if (line.contains(token, ignoreCase = true)) {
                        violations += "${file.relativeTo(sourceRoot())}:${index + 1}  $token  ->  ${line.trim()}"
                    }
                }
            }
        }

        assertTrue(
            "Editorial Bible 1.10 violated — placeholders found:\n" + violations.joinToString("\n"),
            violations.isEmpty(),
        )
    }

    @Test
    fun `the scan actually reaches the source tree`() {
        // A rule that silently scans nothing is worse than no rule at all.
        val files = scannableFiles()
        assertTrue("Placeholder scan found no source files — the scan root is wrong", files.size >= 5)
        assertTrue(
            "Placeholder scan did not reach sautiy-core sources",
            files.any { it.path.contains("sautiy-core") && it.extension == "kt" },
        )
    }

    @Test
    fun `product identity is recorded exactly as the constitution states`() {
        assertTrue(SautiyConstitution.PRODUCT_NAME == "SAUTIY™")
        assertTrue(SautiyConstitution.AUTHOR == "Imam Ahmad Sulaimiy")
        assertTrue(SautiyConstitution.AUTHOR_TITLE.contains("Founder"))
        assertTrue(SautiyConstitution.ABOUT.isNotBlank())
    }

    @Test
    fun `the principles are ordered and complete`() {
        val principles = SautiyConstitution.Principle.entries
        assertTrue("There are seven constitutional principles", principles.size == 7)
        assertTrue(
            "Principle ranks must run 1..7 in declaration order",
            principles.map { it.ordinalRank } == (1..7).toList(),
        )
        assertTrue(principles.all { it.statement.isNotBlank() })
    }
}
