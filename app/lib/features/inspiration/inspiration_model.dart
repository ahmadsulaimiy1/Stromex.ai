import 'package:flutter/material.dart';

enum InspirationCategory { luxury, minimal, vibrant, islamic, corporate }

extension InspirationCategoryLabel on InspirationCategory {
  String get label => switch (this) {
        InspirationCategory.luxury => 'Luxury',
        InspirationCategory.minimal => 'Minimal',
        InspirationCategory.vibrant => 'Vibrant',
        InspirationCategory.islamic => 'Islamic',
        InspirationCategory.corporate => 'Corporate',
      };
}

/// A curated style reference: a real, rendered palette + typography pairing
/// with a short rationale — not a photo. This is the honest MVP shape of
/// "inspiration" (see Known Limitations): a real, useful style board, not
/// the full Pinterest-class discovery feed described in the Phase 2/3
/// architecture, which depends on infrastructure and scale this release
/// deliberately doesn't attempt.
class InspirationMood {
  const InspirationMood({
    required this.title,
    required this.description,
    required this.category,
    required this.palette,
    required this.headlineFont,
    required this.bodyFont,
  });

  final String title;
  final String description;
  final InspirationCategory category;
  final List<Color> palette;
  final String headlineFont;
  final String bodyFont;
}

class InspirationLibrary {
  InspirationLibrary._();

  static const List<InspirationMood> all = [
    InspirationMood(
      title: 'Vision 2030 Editorial',
      description:
          'Deep emerald and warm gold, generous white space, confident serif-leaning headlines. Reads as national, institutional, and premium.',
      category: InspirationCategory.luxury,
      palette: [Color(0xFF0B6E4F), Color(0xFFC9A227), Color(0xFFFAF8F3), Color(0xFF1A1D1B)],
      headlineFont: 'Cairo',
      bodyFont: 'Inter',
    ),
    InspirationMood(
      title: 'Quiet Minimal',
      description:
          'Almost entirely negative space with one confident accent color. Best for single-message announcements that need to breathe.',
      category: InspirationCategory.minimal,
      palette: [Color(0xFFFFFFFF), Color(0xFF1A1D1B), Color(0xFF0B6E4F)],
      headlineFont: 'Inter',
      bodyFont: 'Inter',
    ),
    InspirationMood(
      title: 'Festival Vibrant',
      description:
          'High-energy complementary colors for celebration content — Eid, community events, youth programs. Bold type, playful icon accents.',
      category: InspirationCategory.vibrant,
      palette: [Color(0xFFC9A227), Color(0xFF7A1F3D), Color(0xFF0B6E4F), Color(0xFFFAF8F3)],
      headlineFont: 'Cairo',
      bodyFont: 'Cairo',
    ),
    InspirationMood(
      title: 'Mushaf Calm',
      description:
          'Warm cream, deep ink, and a single gold rule. Restrained and respectful — suited to quotes, reminders, and formal Islamic publications.',
      category: InspirationCategory.islamic,
      palette: [Color(0xFFFAF8F3), Color(0xFF1A1D1B), Color(0xFFC9A227)],
      headlineFont: 'Amiri',
      bodyFont: 'NotoNaskhArabic',
    ),
    InspirationMood(
      title: 'Night Majlis',
      description:
          'Deep charcoal-emerald background with gold linework. Evokes lanterns and evening gatherings — strong for Ramadan and night-event posters.',
      category: InspirationCategory.islamic,
      palette: [Color(0xFF063D2C), Color(0xFFC9A227), Color(0xFFE4C766)],
      headlineFont: 'Amiri',
      bodyFont: 'Cairo',
    ),
    InspirationMood(
      title: 'Corporate Clarity',
      description:
          'Cool neutrals with one structural accent bar. Built for reports, quarterly updates, and anything that needs to look trustworthy fast.',
      category: InspirationCategory.corporate,
      palette: [Color(0xFFFAF8F3), Color(0xFF16324F), Color(0xFF0B6E4F)],
      headlineFont: 'Cairo',
      bodyFont: 'Inter',
    ),
    InspirationMood(
      title: 'Gold Line Luxury',
      description:
          'Near-black background, thin gold rules, small caps labels. For premium invitations and anything that should feel exclusive.',
      category: InspirationCategory.luxury,
      palette: [Color(0xFF121412), Color(0xFFC9A227), Color(0xFFF3F1EA)],
      headlineFont: 'Cairo',
      bodyFont: 'Inter',
    ),
    InspirationMood(
      title: 'Community Warmth',
      description:
          'Soft cream and terracotta-leaning gold with rounded shapes. Friendly and approachable — good for youth and family-facing event flyers.',
      category: InspirationCategory.vibrant,
      palette: [Color(0xFFFAF8F3), Color(0xFFC9A227), Color(0xFF7A1F3D)],
      headlineFont: 'Cairo',
      bodyFont: 'Inter',
    ),
  ];

  static List<InspirationMood> byCategory(InspirationCategory category) =>
      all.where((m) => m.category == category).toList();
}
