import 'package:flutter/material.dart';

enum AiGenerationKind { assistantChat, promptToDesign, flyerGenerator, socialPostGenerator }

/// What the AI Designer returns for a prompt-to-design request: real,
/// applicable content (copy + a palette), not an image — see the
/// Technology Stack Decision Report's reasoning for scoping MVP AI to
/// text/layout generation rather than image synthesis.
class DesignBrief {
  DesignBrief({
    required this.headline,
    required this.subheadline,
    required this.bodyText,
    required this.paletteHex,
    required this.suggestedCategory,
    this.arabicHeadline,
  });

  final String headline;
  final String? arabicHeadline;
  final String subheadline;
  final String bodyText;
  final List<String> paletteHex;
  final String suggestedCategory;

  List<Color> get palette => paletteHex.map((hex) {
        final clean = hex.replaceAll('#', '');
        return Color(int.parse('FF$clean', radix: 16));
      }).toList();

  factory DesignBrief.fromJson(Map<String, dynamic> json) => DesignBrief(
        headline: json['headline'] as String? ?? 'Your Headline',
        arabicHeadline: json['arabic_headline'] as String?,
        subheadline: json['subheadline'] as String? ?? '',
        bodyText: json['body_text'] as String? ?? '',
        paletteHex: (json['palette'] as List<dynamic>?)
                ?.map((e) => e.toString())
                .toList() ??
            const ['#0B6E4F', '#C9A227', '#FAF8F3'],
        suggestedCategory: json['category'] as String? ?? 'general',
      );
}

class ChatMessage {
  ChatMessage({required this.role, required this.text, DateTime? timestamp})
      : timestamp = timestamp ?? DateTime.now();

  final String role; // 'user' | 'assistant'
  final String text;
  final DateTime timestamp;
}

class AiException implements Exception {
  AiException(this.message);
  final String message;

  @override
  String toString() => message;
}
