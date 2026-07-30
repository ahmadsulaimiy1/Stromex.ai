import 'package:flutter/widgets.dart' show TextDirection;
import '../editor/canvas/canvas_model.dart';
import '../templates/template_data.dart';
import '../templates/template_model.dart';
import 'ai_models.dart';

/// Turns an AI-generated [DesignBrief] into a real, editable
/// [CanvasDocument] by populating a matching curated template rather than
/// synthesizing a layout from scratch — the MVP's AI Designer generates
/// copy and a palette (see docs/strategy/06-technology-stack-decision.md);
/// TASMIM's own template craftsmanship supplies the layout.
CanvasDocument applyDesignBrief(DesignBrief brief, CanvasSizePreset requestedPreset) {
  final category = _categoryFor(brief.suggestedCategory);
  final template = _bestTemplate(category, requestedPreset);
  final document = template.build();

  final textObjects = document.objects.whereType<TextObject>().toList()
    ..sort((a, b) => b.fontSize.compareTo(a.fontSize));

  if (textObjects.isNotEmpty) {
    final headline = textObjects.first;
    headline.text =
        (headline.textDirection == TextDirection.rtl && brief.arabicHeadline != null)
            ? brief.arabicHeadline!
            : brief.headline;
  }
  if (textObjects.length > 1 && brief.subheadline.isNotEmpty) {
    textObjects[1].text = brief.subheadline;
  }
  if (textObjects.length > 2 && brief.bodyText.isNotEmpty) {
    textObjects[2].text = brief.bodyText;
  }

  // Only recolor general-purpose templates. Islamic Suite templates keep
  // their curated palette regardless of AI suggestion — see the Islamic
  // Creative Suite governance notes on not letting generation silently
  // override deliberately-considered design choices in that category.
  if (category == TemplateCategory.general && brief.palette.isNotEmpty) {
    document.backgroundColor = brief.palette.last;
  }

  document.title = brief.headline;
  return document;
}

TemplateCategory _categoryFor(String raw) {
  return switch (raw) {
    'islamic-flyer' => TemplateCategory.islamicFlyer,
    'mosque-event' => TemplateCategory.mosqueEvent,
    'dawah-poster' => TemplateCategory.dawahPoster,
    _ => TemplateCategory.general,
  };
}

DesignTemplate _bestTemplate(TemplateCategory category, CanvasSizePreset preset) {
  final targetRatio = preset.width / preset.height;
  var pool = TemplateLibrary.byCategory(category);
  if (pool.isEmpty) pool = TemplateLibrary.all;

  DesignTemplate best = pool.first;
  double bestDiff = double.infinity;
  for (final template in pool) {
    final doc = template.build();
    final diff = (doc.aspectRatio - targetRatio).abs();
    if (diff < bestDiff) {
      bestDiff = diff;
      best = template;
    }
  }
  return best;
}
