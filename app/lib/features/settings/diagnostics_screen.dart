import 'package:flutter/material.dart';
import '../../core/logging/app_logger.dart';

class DiagnosticsScreen extends StatefulWidget {
  const DiagnosticsScreen({super.key});

  @override
  State<DiagnosticsScreen> createState() => _DiagnosticsScreenState();
}

class _DiagnosticsScreenState extends State<DiagnosticsScreen> {
  @override
  Widget build(BuildContext context) {
    final entries = AppLogger.instance.recentEntries.reversed.toList();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Diagnostics'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined),
            onPressed: () {
              AppLogger.instance.clear();
              setState(() {});
            },
          ),
        ],
      ),
      body: entries.isEmpty
          ? Center(
              child: Text('No activity logged yet', style: Theme.of(context).textTheme.bodyMedium),
            )
          : ListView.builder(
              itemCount: entries.length,
              itemBuilder: (context, index) {
                final entry = entries[index];
                final color = switch (entry.level) {
                  LogLevel.error => Colors.red,
                  LogLevel.warning => Colors.orange,
                  LogLevel.info => Theme.of(context).colorScheme.primary,
                  LogLevel.debug => Colors.grey,
                };
                return ListTile(
                  dense: true,
                  leading: Icon(Icons.circle, size: 10, color: color),
                  title: Text(entry.message, style: const TextStyle(fontSize: 13)),
                  subtitle: Text(
                    '${entry.tag} · ${entry.timestamp.toIso8601String()}',
                    style: const TextStyle(fontSize: 11),
                  ),
                );
              },
            ),
    );
  }
}
