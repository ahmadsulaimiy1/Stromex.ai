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

    /**
     * Conventional all-caps markers. Matched case-**sensitively** and on word boundaries:
     * `toDouble` contains the letters of one of these and is not a placeholder, and a scanner
     * that cannot tell the difference gets switched off within a week.
     */
    private val bannedMarkers: List<Regex> = listOf("TO" + "DO", "FIX" + "ME", "XX" + "X", "HA" + "CK")
        .map { Regex("\\b${Regex.escape(it)}\\b") }

    /** Phrases that betray unfinished work whatever their casing. */
    private val bannedPhrases: List<Regex> = listOf(
        "Place" + "holder",
        "Coming " + "Soon",
        "Future " + "Work",
        "Not " + "Implemented",
        "Not " + "Yet Implemented",
        "unimplemented" + "\\(\\)",
        "\\bstub" + "bed\\b",
    ).map { Regex(it, RegexOption.IGNORE_CASE) }

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
                for (pattern in bannedMarkers + bannedPhrases) {
                    val hit = pattern.find(line) ?: continue
                    violations += "${file.relativeTo(sourceRoot())}:${index + 1}  " +
                        "'${hit.value}'  ->  ${line.trim()}"
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
    fun `the scan does not fire on ordinary code that merely contains the letters`() {
        // `toDouble` contains the letters of a banned marker. A scanner that flags it produces
        // noise on every numeric line in the engine and is switched off within a week, which
        // means the rule stops being enforced at all. Word boundaries and case sensitivity are
        // what keep this rule alive.
        val innocent = listOf(
            "val seconds = frameCount.toDouble() / sampleRate",
            "buffer.channels[0].maxOf { abs(it) }.toDouble()",
            "private const val TODAY = 1",
            "fun toDoubleArray(): DoubleArray",
        )
        for (line in innocent) {
            for (pattern in bannedMarkers + bannedPhrases) {
                assertTrue(
                    "False positive: '$line' matched ${pattern.pattern}",
                    pattern.find(line) == null,
                )
            }
        }
    }

    @Test
    fun `the scan does fire on a real placeholder`() {
        val guilty = listOf(
            "// " + "TODO" + ": wire this up",
            "throw NotImplementedError(\"" + "Coming Soon" + "\")",
            "val label = \"" + "Placeholder" + "\"",
        )
        for (line in guilty) {
            val matched = (bannedMarkers + bannedPhrases).any { it.find(line) != null }
            assertTrue("The scan missed a real placeholder: '$line'", matched)
        }
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
