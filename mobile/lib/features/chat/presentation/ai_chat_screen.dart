import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../catalog/presentation/product_detail_screen.dart';

class ChatMessageModel {
  ChatMessageModel({
    required this.isUser,
    required this.text,
    this.suggestedProducts = const [],
    this.suggestedActions = const [],
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  final bool isUser;
  final String text;
  final List<dynamic> suggestedProducts;
  final List<dynamic> suggestedActions;
  final DateTime timestamp;
}

class AiChatScreen extends ConsumerStatefulWidget {
  const AiChatScreen({super.key});

  @override
  ConsumerState<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends ConsumerState<AiChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatMessageModel> _messages = [];
  bool _sending = false;

  static const _quickPrompts = [
    '✨ ¿Cómo funciona el vestidor virtual?',
    '🏬 ¿Dónde quedan sus sucursales?',
    '🏷️ ¿Tienen promociones activas?',
    '👗 ¿Qué vestidos elegantes me recomiendas?',
    '🧥 Muéstrame sacos y abrigos',
  ];

  @override
  void initState() {
    super.initState();
    _messages.add(
      ChatMessageModel(
        isUser: false,
        text:
            '¡Hola! Soy Sofía, tu asesora virtual de estilo en FashionStore. '
            'Puedo ayudarte a encontrar la prenda perfecta, consultar disponibilidad en nuestras sucursales, informarte de promociones o guiarte en el uso de nuestro vestidor virtual con realidad aumentada. ¿Qué buscas hoy?',
        suggestedActions: [
          {'label': 'Vestidor virtual', 'action': 'fitting_room'},
          {'label': 'Ver sucursales', 'action': 'branches'},
          {'label': 'Promociones', 'action': 'promotions'},
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage([String? customText]) async {
    final text = (customText ?? _controller.text).trim();
    if (text.isEmpty || _sending) return;

    if (customText == null) {
      _controller.clear();
    }

    setState(() {
      _messages.add(ChatMessageModel(isUser: true, text: text));
      _sending = true;
    });
    _scrollToBottom();

    try {
      final history = _messages
          .where((m) => m != _messages.last)
          .map(
            (m) => {'role': m.isUser ? 'user' : 'assistant', 'content': m.text},
          )
          .toList();

      final response =
          await ref
                  .read(apiClientProvider)
                  .post('/ai/chat', body: {'message': text, 'history': history})
              as Map<String, dynamic>;

      if (mounted) {
        setState(() {
          _messages.add(
            ChatMessageModel(
              isUser: false,
              text:
                  response['message'] as String? ??
                  'No pude procesar tu solicitud.',
              suggestedProducts:
                  (response['suggested_products'] as List<dynamic>?) ??
                  const [],
              suggestedActions:
                  (response['suggested_actions'] as List<dynamic>?) ?? const [],
            ),
          );
          _sending = false;
        });
        _scrollToBottom();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _messages.add(
            ChatMessageModel(
              isUser: false,
              text:
                  'Lo siento, tuve un inconveniente de conexión. Por favor inténtalo de nuevo.',
            ),
          );
          _sending = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _resetChat() {
    setState(() {
      _messages.clear();
      _messages.add(
        ChatMessageModel(
          isUser: false,
          text:
              '¡Hola de nuevo! Conversación reiniciada. ¿En qué prenda o consulta te puedo colaborar?',
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppColors.goldDeep.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: AppColors.goldDeep,
                size: 20,
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Sofía IA',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
                Text(
                  'Asistente de moda y tienda',
                  style: TextStyle(
                    fontSize: 11,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _resetChat,
            tooltip: 'Reiniciar conversación',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Quick suggestion chips
            SizedBox(
              height: 48,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 6,
                ),
                itemCount: _quickPrompts.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final prompt = _quickPrompts[index];
                  return ActionChip(
                    label: Text(prompt, style: const TextStyle(fontSize: 12)),
                    backgroundColor: Theme.of(
                      context,
                    ).colorScheme.surfaceContainerHighest,
                    side: BorderSide.none,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20),
                    ),
                    onPressed: _sending ? null : () => _sendMessage(prompt),
                  );
                },
              ),
            ),
            const Divider(height: 1),
            // Message list
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.all(AppSpacing.md),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final msg = _messages[index];
                  return _buildMessageItem(msg);
                },
              ),
            ),
            if (_sending)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'Sofía está pensando...',
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
            // Input bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                border: Border(
                  top: BorderSide(
                    color: Theme.of(context).colorScheme.outlineVariant,
                  ),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                      decoration: const InputDecoration(
                        hintText: 'Pregúntale a Sofía...',
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 10,
                        ),
                      ),
                    ),
                  ),
                  IconButton.filled(
                    onPressed: _sending ? null : () => _sendMessage(),
                    icon: const Icon(Icons.send_rounded, size: 18),
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.charcoal,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageItem(ChatMessageModel msg) {
    if (msg.isUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: Container(
          margin: const EdgeInsets.only(bottom: 12, left: 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.charcoal,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(16),
              topRight: Radius.circular(16),
              bottomLeft: Radius.circular(16),
              bottomRight: Radius.circular(4),
            ),
          ),
          child: Text(
            msg.text,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              height: 1.4,
            ),
          ),
        ),
      );
    }

    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16, right: 36),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 14,
                  backgroundColor: AppColors.goldDeep.withValues(alpha: 0.18),
                  child: const Icon(
                    Icons.auto_awesome,
                    size: 16,
                    color: AppColors.goldDeep,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    decoration: BoxDecoration(
                      color: Theme.of(
                        context,
                      ).colorScheme.surfaceContainerHighest,
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(4),
                        topRight: Radius.circular(16),
                        bottomLeft: Radius.circular(16),
                        bottomRight: Radius.circular(16),
                      ),
                    ),
                    child: Text(
                      msg.text,
                      style: const TextStyle(fontSize: 14, height: 1.45),
                    ),
                  ),
                ),
              ],
            ),
            // Product suggestions if any
            if (msg.suggestedProducts.isNotEmpty) ...[
              const SizedBox(height: 10),
              Padding(
                padding: const EdgeInsets.only(left: 36),
                child: SizedBox(
                  height: 175,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: msg.suggestedProducts.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 10),
                    itemBuilder: (context, i) {
                      final p =
                          msg.suggestedProducts[i] as Map<String, dynamic>;
                      return _buildProductCard(p);
                    },
                  ),
                ),
              ),
            ],
            // Suggested action chips if any
            if (msg.suggestedActions.isNotEmpty) ...[
              const SizedBox(height: 8),
              Padding(
                padding: const EdgeInsets.only(left: 36),
                child: Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    for (final action in msg.suggestedActions)
                      ActionChip(
                        label: Text(
                          action['label'] as String? ?? '',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        avatar: const Icon(Icons.arrow_forward, size: 14),
                        onPressed: () =>
                            _sendMessage(action['label'] as String),
                      ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProductCard(Map<String, dynamic> product) {
    final name = product['name'] as String? ?? 'Prenda';
    final price = product['base_price']?.toString() ?? '0.00';
    final id = product['id'] as int?;

    return Container(
      width: 140,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        boxShadow: [BoxStyle.soft(Theme.of(context).colorScheme.shadow)],
      ),
      padding: const EdgeInsets.all(10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                height: 60,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.checkroom_outlined,
                  size: 30,
                  color: AppColors.charcoalMuted,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                name,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '$price BOB',
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.goldDeep,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          if (id != null)
            SizedBox(
              width: double.infinity,
              height: 28,
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  padding: EdgeInsets.zero,
                  visualDensity: VisualDensity.compact,
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ProductDetailScreen(productId: id),
                    ),
                  );
                },
                child: const Text('Ver prenda', style: TextStyle(fontSize: 11)),
              ),
            ),
        ],
      ),
    );
  }
}

class BoxStyle {
  static BoxShadow soft(Color color) {
    return BoxShadow(
      color: color.withValues(alpha: 0.04),
      blurRadius: 8,
      offset: const Offset(0, 2),
    );
  }
}
