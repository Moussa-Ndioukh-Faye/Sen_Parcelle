// lib/features/messages/presentation/screens/messages_screen.dart
// ═════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:sen_parcelle/core/theme/app_theme.dart';

class MessagesScreen extends StatelessWidget {
  const MessagesScreen({super.key});

  static final _demoMessages = [
    _DemoConv('Aminata Diop', 'Bonjour, le terrain est encore disponible ?',
      '10:24', 2, Colors.amber),
    _DemoConv('Ibrahima Seck', 'D\'accord pour la visite mercredi',
      'Hier', 0, Colors.blue),
    _DemoConv('Fatou Ba', 'Merci pour les informations',
      'Lun', 0, Colors.purple),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Messages'),
        actions: [
          IconButton(icon: const Icon(Icons.edit_outlined), onPressed: () {}),
        ],
      ),
      body: ListView.separated(
        itemCount: _demoMessages.length,
        separatorBuilder: (_, __) => const Divider(height: 1, indent: 72),
        itemBuilder: (_, i) {
          final conv = _demoMessages[i];
          return ListTile(
            onTap: () => context.push('/chat/${i+1}'),
            leading: CircleAvatar(
              backgroundColor: conv.color,
              radius: 24,
              child: Text(conv.name[0],
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
            title: Text(conv.name,
              style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text(conv.lastMsg,
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppTheme.muted, fontSize: 13)),
             trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(conv.time, style: TextStyle(color: AppTheme.muted, fontSize: 11)),
                 if (conv.unread > 0) ...[
                   const SizedBox(height: 4),
                   Container(
                     padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                     decoration: BoxDecoration(
                       color: AppTheme.green,
                       borderRadius: BorderRadius.circular(10),
                     ),
                     child: Text('${conv.unread}',
                       style: const TextStyle(color: Colors.white,
                         fontSize: 11, fontWeight: FontWeight.bold)),
                   ),
                 ],
               ],
             ),
          );
        },
      ),
    );
  }
}

class _DemoConv {
  final String name, lastMsg, time;
  final int unread;
  final Color color;
  const _DemoConv(this.name, this.lastMsg, this.time, this.unread, this.color);
}


// ═══════════════════════════════════════════════════════════════