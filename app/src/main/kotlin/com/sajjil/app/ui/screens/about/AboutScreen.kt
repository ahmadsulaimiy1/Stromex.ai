package com.sajjil.app.ui.screens.about

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.sajjil.app.R
import com.sajjil.app.ui.components.GlassCard

private data class CoreValue(val name: String, val description: String)

private val CORE_VALUES = listOf(
    CoreValue("Excellence", "Pursuing the highest standards in audio quality, engineering, performance, and user experience."),
    CoreValue("Innovation", "Transforming advanced technologies into practical tools that solve real-world problems."),
    CoreValue("Simplicity", "Making sophisticated capabilities accessible through intuitive and seamless experiences."),
    CoreValue("Integrity", "Maintaining transparency, engineering honesty, and user trust."),
    CoreValue("Accessibility", "Providing powerful tools that can be used by people of all skill levels."),
)

private val SUPPORTED_USE_CASES = listOf(
    "Qur'an recitation and memorisation projects",
    "Islamic lectures and educational content",
    "Nasheed production",
    "Podcasts and broadcasting",
    "Audiobooks and voiceovers",
    "Academic recordings",
    "Professional speeches and presentations",
    "Institutional and media production workflows",
)

private val ENGINEERING_OBJECTIVES = listOf(
    "Better audio quality",
    "Faster workflows",
    "Greater reliability",
    "Improved user experience",
    "Increased productivity",
)

/**
 * The platform's own account of itself: mission, values, and the leadership
 * behind it. Static, offline, hand-authored content — nothing here is
 * generated or fetched.
 */
@Composable
fun AboutScreen(modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("About SAJJIL", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.SemiBold)
                Text(
                    "SAJJIL™ 1.0.0",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }

        item {
            BodyText(
                "SAJJIL™ is a next-generation audio recording, enhancement, transcription, and " +
                    "production platform designed to make professional-quality audio creation " +
                    "accessible to everyone.",
            )
        }

        item {
            BodyText(
                "Built with a vision of excellence, simplicity, and innovation, SAJJIL combines " +
                    "advanced audio engineering, intelligent speech technologies, elegant design, " +
                    "and user-centred workflows to empower creators, educators, scholars, reciters, " +
                    "broadcasters, podcasters, institutions, and professionals worldwide.",
            )
        }

        item {
            BodyText(
                "Unlike conventional recording applications, SAJJIL is engineered as a complete " +
                    "audio-production ecosystem — enabling users to record, enhance, refine, " +
                    "transcribe, organise, analyse, master, archive, and publish audio from a " +
                    "unified platform.",
            )
        }

        item {
            SectionCard(title = "The platform is particularly designed to support") {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    SUPPORTED_USE_CASES.forEach { BulletLine(it) }
                }
            }
        }

        item {
            PhilosophyQuote(
                "Professional results. Minimal effort. Maximum elegance.",
            )
        }

        item {
            BodyText(
                "Every component of the platform is designed to reduce complexity while " +
                    "increasing capability, ensuring that both beginners and professionals can " +
                    "achieve exceptional outcomes with confidence.",
            )
        }

        item { SectionDivider() }

        item {
            SectionCard(title = "Vision") {
                BodyText(
                    "To become the world's most trusted and innovative audio-production " +
                        "platform, delivering studio-quality experiences through intelligent " +
                        "technology, seamless workflows, and uncompromising engineering standards.",
                )
            }
        }

        item {
            SectionCard(title = "Mission") {
                BodyText(
                    "To empower individuals and institutions to create beautiful, clear, " +
                        "impactful, and professionally refined audio content through technology " +
                        "that is powerful, accessible, reliable, and elegant.",
                )
            }
        }

        item {
            SectionCard(title = "Core Values") {
                Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    CORE_VALUES.forEach { value ->
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Text(value.name, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.primary)
                            Text(value.description, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }
        }

        item { SectionDivider() }

        item { LeadershipCard() }

        item { SectionDivider() }

        item {
            SectionCard(title = "Engineering Philosophy") {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    BodyText("SAJJIL is built on the principle that technology should not overwhelm the user.")
                    BodyText("Every feature must contribute to one or more of the following objectives:")
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        ENGINEERING_OBJECTIVES.forEach { BulletLine(it) }
                    }
                    BodyText(
                        "Features that do not meaningfully improve outcomes are deliberately excluded.",
                        emphasis = true,
                    )
                }
            }
        }

        item { SectionDivider() }

        item {
            Column(
                modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text("SAJJIL™", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text("Designed for creators.", style = MaterialTheme.typography.bodyMedium, fontStyle = FontStyle.Italic)
                Text("Built for excellence.", style = MaterialTheme.typography.bodyMedium, fontStyle = FontStyle.Italic)
                Text("Engineered for the future.", style = MaterialTheme.typography.bodyMedium, fontStyle = FontStyle.Italic)
                Text(
                    "Developed by Imam Ahmad Sulaimiy.",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(top = 8.dp),
                )
                Text("StromeX Company LTD", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

@Composable
private fun LeadershipCard() {
    GlassCard {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Development Leadership", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Image(
                    painter = painterResource(R.drawable.founder_ahmad_sulaimiy),
                    contentDescription = "Imam Ahmad Sulaimiy, founder of SAJJIL",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.size(84.dp).clip(CircleShape),
                )
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text("Imam Ahmad Sulaimiy", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    Text(
                        "Senior Software Engineer · Educational Technology Innovator · Islamic Scholar",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Text(
                        "Digital Transformation Strategist · Founder of multiple educational and technology initiatives",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
            BodyText(
                "His vision for SAJJIL is to create a world-class audio platform that combines " +
                    "cutting-edge technology with exceptional usability, serving creators, " +
                    "educators, institutions, scholars, and professionals across the globe.",
            )
        }
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable () -> Unit) {
    Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            content()
        }
    }
}

@Composable
private fun PhilosophyQuote(text: String) {
    Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
        Text(
            text,
            modifier = Modifier.fillMaxWidth().padding(20.dp),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            fontStyle = FontStyle.Italic,
            color = MaterialTheme.colorScheme.onPrimaryContainer,
        )
    }
}

@Composable
private fun BodyText(text: String, emphasis: Boolean = false) {
    Text(
        text,
        style = MaterialTheme.typography.bodyMedium,
        fontWeight = if (emphasis) FontWeight.SemiBold else FontWeight.Normal,
    )
}

@Composable
private fun BulletLine(text: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("•", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun SectionDivider() {
    Surface(
        modifier = Modifier.fillMaxWidth().height(1.dp),
        color = MaterialTheme.colorScheme.outline.copy(alpha = 0.3f),
    ) {}
}
