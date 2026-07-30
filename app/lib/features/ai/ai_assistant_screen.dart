import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'ai_models.dart';
import 'ai_service.dart';

class AiAssistantScreen extends StatefulWidget {
  const AiAssistantScreen({super.key});

  @override
  State<AiAssistantScreen> createState() => _AiAssistantScreenState();
}

class _AiAssistantScreenState extends State<AiAssistantScreen> {
  final List<ChatMessage> _messages = [];
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  bool _sending = false;
  bool? _hasKey;

  @override
  void initState() {
    super.initState();
    _checkKey();
  }

  Future<void> _checkKey() async {
    final has = await context.read<AiService>().hasApiKey();
    if (mounted) setState(() => _hasKey = has);
  }

  Future<void> _send() async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _messages.add(ChatMessage(role: 'user', text: text));
      _sending = true;
      _inputController.clear();
    });
    _scrollToBottom();
    try {
      final reply = await context.read<AiService>().assistantReply(_messages);
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', text: reply));
      });
    } on AiException catch (e) {
      setState(() {
        _messages.add(ChatMessage(role: 'assistant', text: '⚠️ ${e.message}'));
      });
    } finally {
      if (mounted) setState(() => _sending = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_hasKey == false) {
      return Scaffold(
        appBar: AppBar(title: const Text('AI Design Assistant')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.vpn_key_rounded, size: 48, color: theme.colorScheme.primary),
                const SizedBox(height: 16),
                Text('Add your API key', style: theme.textTheme.titleLarge, textAlign: TextAlign.center),
                const SizedBox(height: 8),
                Text(
                  'TASMIM\'s AI features use your own Anthropic API key, kept encrypted on this device. Add one in Settings to start.',
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: () => context.push('/settings'),
                  child: const Text('Open Settings'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('AI Design Assistant')),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text(
                        'Ask about layout, color, typography, or hierarchy — '
                        'the TASMIM AI Design Assistant gives concrete, practical advice.',
                        style: theme.textTheme.bodyMedium
                            ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final message = _messages[index];
                      final isUser = message.role == 'user';
                      return Align(
                        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
                          decoration: BoxDecoration(
                            color: isUser
                                ? theme.colorScheme.primary
                                : theme.colorScheme.onSurface.withValues(alpha: 0.06),
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: Text(
                            message.text,
                            style: TextStyle(color: isUser ? Colors.white : theme.colorScheme.onSurface),
                          ),
                        ),
                      );
                    },
                  ),
          ),
          if (_sending) const LinearProgressIndicator(minHeight: 2),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputController,
                      decoration: const InputDecoration(hintText: 'Ask for design advice...'),
                      onSubmitted: (_) => _send(),
                      textInputAction: TextInputAction.send,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _sending ? null : _send,
                    icon: const Icon(Icons.send_rounded),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
