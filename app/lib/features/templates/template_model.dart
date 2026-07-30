import 'package:flutter/material.dart';
import '../editor/canvas/canvas_model.dart';

enum TemplateCategory {
  general,
  socialMedia,
  islamicFlyer,
  mosqueEvent,
  dawahPoster,
}

extension TemplateCategoryLabel on TemplateCategory {
  String get label => switch (this) {
        TemplateCategory.general => 'General',
        TemplateCategory.socialMedia => 'Social Media',
        TemplateCategory.islamicFlyer => 'Islamic Flyers',
        TemplateCategory.mosqueEvent => 'Mosque Events',
        TemplateCategory.dawahPoster => "Da'wah Posters",
      };

  IconData get icon => switch (this) {
        TemplateCategory.general => Icons.dashboard_customize_rounded,
        TemplateCategory.socialMedia => Icons.smartphone_rounded,
        TemplateCategory.islamicFlyer => Icons.nights_stay_rounded,
        TemplateCategory.mosqueEvent => Icons.mosque_rounded,
        TemplateCategory.dawahPoster => Icons.campaign_rounded,
      };
}

/// A curated, built-in design. `build()` returns a fresh [CanvasDocument]
/// each call (never a shared mutable instance) so opening the same
/// template twice never lets one edit bleed into the other.
class DesignTemplate {
  const DesignTemplate({
    required this.id,
    required this.name,
    required this.category,
    required this.build,
  });

  final String id;
  final String name;
  final TemplateCategory category;
  final CanvasDocument Function() build;
}
