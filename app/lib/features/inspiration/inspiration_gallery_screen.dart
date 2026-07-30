import 'package:flutter/material.dart';
import 'inspiration_model.dart';

class InspirationGalleryScreen extends StatefulWidget {
  const InspirationGalleryScreen({super.key});

  @override
  State<InspirationGalleryScreen> createState() => _InspirationGalleryScreenState();
}

class _InspirationGalleryScreenState extends State<InspirationGalleryScreen> {
  InspirationCategory? _filter;

  @override
  Widget build(BuildContext context) {
    final moods = _filter == null
        ? InspirationLibrary.all
        : InspirationLibrary.byCategory(_filter!);

    return Scaffold(
      appBar: AppBar(title: const Text('Inspiration')),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
            child: Text(
              'A curated set of color and typography moods to guide your next design.',
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6)),
            ),
          ),
          SizedBox(
            height: 56,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: ChoiceChip(
                    label: const Text('All'),
                    selected: _filter == null,
                    onSelected: (_) => setState(() => _filter = null),
                  ),
                ),
                for (final category in InspirationCategory.values)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: ChoiceChip(
                      label: Text(category.label),
                      selected: _filter == category,
                      onSelected: (_) => setState(() => _filter = category),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              itemCount: moods.length,
              itemBuilder: (context, index) => _MoodCard(mood: moods[index]),
            ),
          ),
        ],
      ),
    );
  }
}

class _MoodCard extends StatelessWidget {
  const _MoodCard({required this.mood});

  final InspirationMood mood;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(mood.title, style: Theme.of(context).textTheme.titleMedium),
                ),
                Chip(
                  label: Text(mood.category.label),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: mood.palette
                  .map((c) => Expanded(
                        child: Container(
                          height: 48,
                          margin: const EdgeInsets.only(right: 6),
                          decoration: BoxDecoration(
                            color: c,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.black.withValues(alpha: 0.06)),
                          ),
                        ),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 12),
            Text(
              mood.description,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7)),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Icon(Icons.title_rounded, size: 16, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 6),
                Text('${mood.headlineFont} + ${mood.bodyFont}',
                    style: Theme.of(context).textTheme.labelMedium),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
