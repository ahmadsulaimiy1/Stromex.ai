import 'package:flutter/material.dart';

Future<String?> showTextEditDialog(BuildContext context, String initialText) {
  final controller = TextEditingController(text: initialText);
  return showDialog<String>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Edit text'),
      content: TextField(
        controller: controller,
        autofocus: true,
        maxLines: 5,
        minLines: 1,
        textDirection: TextDirection.rtl == Directionality.of(context)
            ? TextDirection.rtl
            : TextDirection.ltr,
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () => Navigator.of(context).pop(controller.text),
          child: const Text('Done'),
        ),
      ],
    ),
  );
}
