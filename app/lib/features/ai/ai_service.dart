import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/logging/app_logger.dart';
import '../../core/storage/secure_storage_service.dart';
import 'ai_models.dart';

/// TASMIM's AI Design Assistant, implemented bring-your-own-key against
/// the Anthropic API — per the Technology Stack Decision Report, TASMIM
/// never ships or proxies a shared key; the user's key stays on-device
/// and every request goes straight from the app to the provider.
class AiService {
  AiService(this._secureStorage);

  final SecureStorageService _secureStorage;
  static const _tag = 'AiService';
  static const _endpoint = 'https://api.anthropic.com/v1/messages';
  static const _model = 'claude-sonnet-4-5-20250929';
  static const _apiVersion = '2023-06-01';

  Future<bool> hasApiKey() async {
    final key = await _secureStorage.read(SecureStorageService.keyAiApiKey);
    return key != null && key.trim().isNotEmpty;
  }

  Future<void> setApiKey(String key) async {
    await _secureStorage.write(SecureStorageService.keyAiApiKey, key.trim());
  }

  Future<void> clearApiKey() async {
    await _secureStorage.delete(SecureStorageService.keyAiApiKey);
  }

  Future<String> _requireApiKey() async {
    final key = await _secureStorage.read(SecureStorageService.keyAiApiKey);
    if (key == null || key.trim().isEmpty) {
      throw AiException(
          'Add your Anthropic API key in Settings to use AI features.');
    }
    return key.trim();
  }

  Future<Map<String, dynamic>> _send({
    required String system,
    required List<Map<String, String>> messages,
    int maxTokens = 1024,
  }) async {
    final apiKey = await _requireApiKey();
    try {
      final response = await http
          .post(
            Uri.parse(_endpoint),
            headers: {
              'content-type': 'application/json',
              'x-api-key': apiKey,
              'anthropic-version': _apiVersion,
            },
            body: jsonEncode({
              'model': _model,
              'max_tokens': maxTokens,
              'system': system,
              'messages': messages
                  .map((m) => {'role': m['role'], 'content': m['content']})
                  .toList(),
            }),
          )
          .timeout(const Duration(seconds: 45));

      if (response.statusCode == 401) {
        throw AiException('That API key was rejected. Check it in Settings.');
      }
      if (response.statusCode == 429) {
        throw AiException('Rate limited by the AI provider. Try again shortly.');
      }
      if (response.statusCode >= 400) {
        AppLogger.instance
            .error(_tag, 'AI request failed: ${response.statusCode} ${response.body}');
        throw AiException('The AI request failed (${response.statusCode}).');
      }
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on AiException {
      rethrow;
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'AI request error', e, st);
      throw AiException('Could not reach the AI provider. Check your connection.');
    }
  }

  String _extractText(Map<String, dynamic> response) {
    final content = response['content'] as List<dynamic>?;
    if (content == null || content.isEmpty) return '';
    final first = content.first as Map<String, dynamic>;
    return first['text'] as String? ?? '';
  }

  /// Free-form design assistant chat (AI Designer, generalist entry point).
  Future<String> assistantReply(List<ChatMessage> history) async {
    final response = await _send(
      system:
          'You are the TASMIM AI Design Assistant, a helpful and concise creative '
          'partner for graphic design. Give practical, specific design advice '
          '(layout, color, typography, hierarchy). Keep replies under 120 words '
          'unless asked for more detail. When relevant to Islamic or Arabic design '
          'contexts, be respectful and accurate, and note that anything involving '
          'Qur\'anic or liturgical text should be reviewed by a qualified scholar '
          'rather than generated freely.',
      messages: history
          .map((m) => {'role': m.role, 'content': m.text})
          .toList(),
      maxTokens: 500,
    );
    return _extractText(response).trim();
  }

  /// Prompt-to-design: returns structured copy + a palette to populate a
  /// template with. This is TASMIM's MVP AI Designer — see
  /// docs/strategy/06-technology-stack-decision.md for why generation is
  /// scoped to text/palette rather than image synthesis in this release.
  Future<DesignBrief> generateDesignBrief({
    required String prompt,
    required String targetFormat,
    bool includeArabic = false,
  }) async {
    final system = '''
You are the TASMIM AI Designer. Given a short brief, respond with ONLY a
single JSON object (no prose, no markdown fences) with these exact keys:
{
  "headline": "short, punchy headline, max 6 words",
  "arabic_headline": ${includeArabic ? '"an accurate Arabic translation or equivalent of the headline, max 6 words"' : 'null'},
  "subheadline": "supporting line, max 12 words",
  "body_text": "one short sentence of body copy, max 25 words",
  "palette": ["#RRGGBB", "#RRGGBB", "#RRGGBB"],
  "category": "one of: general, islamic-flyer, mosque-event, dawah-poster"
}
The design is a $targetFormat. Palette should be tasteful, cohesive, and
suited to a premium, elegant brand identity. If the brief is about Islamic,
Ramadan, Eid, mosque, or da'wah content, pick the matching category and use
respectful, accurate language — never invent or paraphrase Qur'anic verses.
''';
    final response = await _send(
      system: system,
      messages: [
        {'role': 'user', 'content': prompt}
      ],
      maxTokens: 400,
    );
    final text = _extractText(response).trim();
    final jsonText = _extractJsonObject(text);
    try {
      final decoded = jsonDecode(jsonText) as Map<String, dynamic>;
      return DesignBrief.fromJson(decoded);
    } catch (e, st) {
      AppLogger.instance.error(_tag, 'Failed to parse design brief: $text', e, st);
      throw AiException('The AI response could not be understood. Try rephrasing.');
    }
  }

  String _extractJsonObject(String text) {
    final start = text.indexOf('{');
    final end = text.lastIndexOf('}');
    if (start == -1 || end == -1 || end < start) return text;
    return text.substring(start, end + 1);
  }
}
