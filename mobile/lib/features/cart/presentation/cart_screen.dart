import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_stripe/flutter_stripe.dart' hide Card;

import '../../../core/payment_config.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';

class CartScreen extends ConsumerStatefulWidget {
  const CartScreen({super.key});
  @override
  ConsumerState<CartScreen> createState() => _CartScreenState();
}

class _CartScreenState extends ConsumerState<CartScreen> {
  Map<String, dynamic>? cart;
  List<Map<String, dynamic>> branches = [];
  int? selectedBranchId;
  String fulfillmentType = 'PICKUP';
  final shippingDetails = <String, String>{
    'recipient_name': '',
    'recipient_ci': '',
    'recipient_phone': '',
    'department_or_city': '',
    'zone': '',
    'street': '',
    'house_number': '',
    'reference': '',
  };
  String selectedPaymentMethod = 'CARD';
  bool loading = true;
  bool paying = false;
  bool cardComplete = false;
  bool loadingQr = false;
  Map<String, dynamic>? qrPayment;
  String message = '';
  final CardEditController cardController = CardEditController();

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    cardController.dispose();
    super.dispose();
  }

  Future<void> load() async {
    try {
      final cartFuture = ref.read(cartRepositoryProvider).get();
      final branchesFuture = ref.read(catalogRepositoryProvider).getBranches();
      final results = await Future.wait([cartFuture, branchesFuture]);
      if (mounted) {
        final branchList = results[1] as List<Map<String, dynamic>>;
        setState(() {
          cart = results[0] as Map<String, dynamic>;
          branches = branchList;
          if (selectedBranchId == null && branchList.isNotEmpty) {
            selectedBranchId = branchList.first['id'] as int;
          }
          loading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          loading = false;
          message = 'No pudimos cargar tu carrito o sucursales.';
        });
      }
    }
  }

  Future<void> remove(int id) async {
    final result = await ref.read(cartRepositoryProvider).remove(id);
    if (mounted) setState(() => cart = result);
  }

  Future<void> checkout() async {
    if (selectedPaymentMethod == 'QR') {
      await confirmQrPayment();
      return;
    }
    // Local APKs without a public Stripe key use the signed electronic
    // fallback instead of exposing a button that can only fail.
    if (!PaymentConfig.isStripeConfigured) {
      await demoCheckout();
      return;
    }
    if (PaymentConfig.provider != PaymentProvider.stripe) {
      await demoCheckout();
      return;
    }
    if (!_validateCheckout()) return;
    setState(() {
      paying = true;
      message = '';
    });
    try {
      final sale = await ref
          .read(cartRepositoryProvider)
          .purchase(
            selectedBranchId!,
            fulfillmentType: fulfillmentType == 'DELIVERY' ? 'DELIVERY' : null,
            shippingDetails: fulfillmentType == 'DELIVERY'
                ? Map<String, dynamic>.from(shippingDetails)
                : null,
          );
      final intent = await ref
          .read(cartRepositoryProvider)
          .createStripeIntent(
            sale['id'] as int,
            'mobile-stripe-${sale['id']}-${DateTime.now().millisecondsSinceEpoch}',
          );
      final clientSecret = intent['client_secret'] as String?;
      final paymentIntentId = intent['payment_intent_id'] as String?;
      if (clientSecret == null ||
          clientSecret.isEmpty ||
          paymentIntentId == null ||
          paymentIntentId.isEmpty) {
        throw StateError('Stripe intent response is missing client secret.');
      }

      // The backend confirms simulated intents directly. PaymentSheet is only
      // used when the backend returns a real Stripe client secret.
      if (clientSecret.startsWith('pi_mock_')) {
        final confirmed = await ref
            .read(cartRepositoryProvider)
            .confirmStripePayment(clientSecret.split('_secret_').first);
        if (mounted) {
          setState(() {
            paying = false;
            message =
                'Compra ${confirmed['order_number'] ?? sale['order_number']} confirmada con tarjeta. ${_fulfillmentSummary()}';
          });
          await load();
        }
        return;
      }

      if (!PaymentConfig.isStripeConfigured) {
        throw StateError(
          'El pago con tarjeta no está configurado en esta instalación.',
        );
      }

      if (!cardComplete) {
        throw StateError('Completá los datos de la tarjeta para continuar.');
      }

      final payment = await Stripe.instance.confirmPayment(
        paymentIntentClientSecret: clientSecret,
        data: PaymentMethodParams.card(paymentMethodData: PaymentMethodData()),
      );
      if (payment.status == PaymentIntentsStatus.RequiresAction) {
        await Stripe.instance.handleNextAction(clientSecret);
      }
      final confirmed = await ref
          .read(cartRepositoryProvider)
          .confirmStripePayment(paymentIntentId);
      if (mounted) {
        setState(() {
          paying = false;
          message =
              'Compra ${confirmed['order_number'] ?? sale['order_number']} confirmada con tarjeta. ${_fulfillmentSummary()}';
        });
        await load();
      }
    } on StripeException catch (e) {
      if (mounted) {
        setState(() {
          paying = false;
          message =
              e.error.localizedMessage ?? 'Pago Stripe cancelado o rechazado.';
        });
      }
    } catch (error, stackTrace) {
      debugPrint('Stripe checkout failed: $error');
      debugPrintStack(stackTrace: stackTrace);
      if (mounted) {
        setState(() {
          paying = false;
          message = error.toString();
        });
      }
    }
  }

  Future<void> prepareQrPayment() async {
    if (!_validateCheckout() || loadingQr || qrPayment != null) return;
    setState(() {
      loadingQr = true;
      message = '';
    });
    try {
      final sale = await ref
          .read(cartRepositoryProvider)
          .purchase(
            selectedBranchId!,
            fulfillmentType: fulfillmentType == 'DELIVERY' ? 'DELIVERY' : null,
            shippingDetails: fulfillmentType == 'DELIVERY'
                ? Map<String, dynamic>.from(shippingDetails)
                : null,
          );
      final payment = await ref
          .read(cartRepositoryProvider)
          .generateQrPayment(sale['id'] as int);
      if (mounted) {
        setState(() {
          qrPayment = payment;
          loadingQr = false;
        });
      }
    } catch (error, stackTrace) {
      debugPrint('QR checkout failed: $error');
      debugPrintStack(stackTrace: stackTrace);
      if (mounted) {
        setState(() {
          loadingQr = false;
          message = 'No pudimos generar el código QR. Intentá nuevamente.';
        });
      }
    }
  }

  Future<void> confirmQrPayment() async {
    if (qrPayment == null || paying) return;
    setState(() {
      paying = true;
      message = '';
    });
    try {
      final confirmed = await ref
          .read(cartRepositoryProvider)
          .confirmQrTransfer(
            qrPayment!['transaction_reference'] as String,
            qrPayment!['amount'].toString(),
          );
      if (mounted) {
        setState(() {
          paying = false;
          qrPayment = null;
          message =
              'Compra ${confirmed['order_number']} confirmada con QR. ${_fulfillmentSummary()}';
        });
        await load();
      }
    } catch (error, stackTrace) {
      debugPrint('QR confirmation failed: $error');
      debugPrintStack(stackTrace: stackTrace);
      if (mounted) {
        setState(() {
          paying = false;
          message =
              'No pudimos confirmar el pago QR. Verificá la transferencia.';
        });
      }
    }
  }

  Future<void> demoCheckout() async {
    if (!_validateCheckout()) return;
    setState(() {
      paying = true;
      message = '';
    });
    try {
      final sale = await ref
          .read(cartRepositoryProvider)
          .purchase(
            selectedBranchId!,
            fulfillmentType: fulfillmentType == 'DELIVERY' ? 'DELIVERY' : null,
            shippingDetails: fulfillmentType == 'DELIVERY'
                ? Map<String, dynamic>.from(shippingDetails)
                : null,
          );
      final payment = await ref
          .read(cartRepositoryProvider)
          .pay(
            sale['id'] as int,
            'mobile-demo-$selectedPaymentMethod-${sale['id']}-${DateTime.now().millisecondsSinceEpoch}',
          );
      await ref
          .read(cartRepositoryProvider)
          .approve(
            payment['transaction_reference'] as String,
            sale['total'].toString(),
          );
      if (mounted) {
        setState(() {
          paying = false;
          message = selectedPaymentMethod == 'CARD'
              ? 'Compra ${sale['order_number']} confirmada con tarjeta en modo local. ${_fulfillmentSummary()}'
              : 'Compra ${sale['order_number']} confirmada (${_paymentLabel(selectedPaymentMethod)}). ${_fulfillmentSummary()}';
        });
        await load();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          paying = false;
          message = 'No pudimos completar la demostración.';
        });
      }
    }
  }

  bool _validateCheckout() {
    if (selectedBranchId == null || selectedBranchId! <= 0 || cart == null) {
      setState(
        () => message = fulfillmentType == 'DELIVERY'
            ? 'Seleccioná la sucursal que preparará el delivery.'
            : 'Seleccioná la sucursal de retiro.',
      );
      return false;
    }
    if (fulfillmentType != 'DELIVERY') return true;
    const labels = {
      'recipient_name': 'nombre del destinatario',
      'recipient_ci': 'CI',
      'recipient_phone': 'teléfono',
      'department_or_city': 'departamento o ciudad',
      'zone': 'zona',
      'street': 'calle',
      'house_number': 'número de casa',
      'reference': 'referencia',
    };
    final missing = labels.entries
        .where((entry) => (shippingDetails[entry.key] ?? '').trim().isEmpty)
        .map((entry) => entry.value)
        .toList();
    if (missing.isNotEmpty) {
      setState(
        () =>
            message = 'Completá los datos de delivery: ${missing.join(', ')}.',
      );
      return false;
    }
    return true;
  }

  String _fulfillmentSummary() {
    if (fulfillmentType != 'DELIVERY') {
      return 'Retiro en sucursal seleccionada.';
    }
    return 'Delivery para ${shippingDetails['recipient_name']} en ${shippingDetails['street']} ${shippingDetails['house_number']}, ${shippingDetails['zone']}.';
  }

  String _paymentLabel(String code) {
    switch (code) {
      case 'CARD':
        return 'Tarjeta de crédito';
      case 'QR':
        return 'Pago QR Simple';
      case 'TRANSFER':
        return 'Transferencia bancaria';
      default:
        return code;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Scaffold(
        body: FashionState(
          icon: Icons.shopping_bag_outlined,
          title: 'Revisando tu selección',
          message: 'Estamos actualizando tu carrito.',
        ),
      );
    }
    final items = (cart?['items'] as List<dynamic>?) ?? const [];
    final total = cart?['total']?.toString() ?? '0.00';
    return Scaffold(
      appBar: AppBar(title: const Text('CARRITO')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          const FashionSectionHeader(
            eyebrow: 'Checkout',
            title: 'Confirmá tu compra.',
            body:
                'Elegí retiro o delivery, mantené la sucursal como origen de inventario y pagá con tarjeta.',
          ),
          const SizedBox(height: AppSpacing.lg),
          if (message.isNotEmpty) ...[
            FashionMessageCard(message: message, icon: Icons.info_outline),
            const SizedBox(height: AppSpacing.md),
          ],
          if (items.isEmpty)
            message.toLowerCase().contains('confirmada')
                ? _confirmationState(context)
                : const FashionState(
                    icon: Icons.shopping_bag_outlined,
                    title: 'Tu carrito está vacío',
                    message:
                        'Agregá una prenda desde el catálogo para continuar.',
                  )
          else ...[
            for (final raw in items) ...[
              _item(raw as Map<String, dynamic>),
              const SizedBox(height: AppSpacing.sm),
            ],
            const SizedBox(height: AppSpacing.lg),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Total',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Text(
                          '$total BOB',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.md),
                    StatusPill(
                      label: PaymentConfig.isStripeConfigured
                          ? 'Pago con tarjeta configurado'
                          : 'Pago con tarjeta en modo local',
                      tone: PaymentConfig.isStripeConfigured
                          ? StatusTone.success
                          : StatusTone.warning,
                    ),
                    const SizedBox(height: AppSpacing.md),
                    if (branches.isNotEmpty)
                      DropdownButtonFormField<int>(
                        initialValue: selectedBranchId,
                        decoration: InputDecoration(
                          labelText: fulfillmentType == 'DELIVERY'
                              ? 'Sucursal de origen para inventario'
                              : 'Sucursal de retiro',
                          prefixIcon: Icon(Icons.storefront_outlined),
                        ),
                        items: [
                          for (final b in branches)
                            DropdownMenuItem<int>(
                              value: b['id'] as int,
                              child: Text(b['name'] as String),
                            ),
                        ],
                        onChanged: (val) {
                          setState(() {
                            selectedBranchId = val;
                            qrPayment = null;
                          });
                          if (selectedPaymentMethod == 'QR' && val != null) {
                            prepareQrPayment();
                          }
                        },
                      )
                    else
                      const Text(
                        'Cargando sucursales...',
                        style: TextStyle(color: Colors.grey, fontSize: 12),
                      ),
                    const SizedBox(height: AppSpacing.md),
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(
                          value: 'PICKUP',
                          label: Text('Retiro'),
                          icon: Icon(Icons.storefront_outlined),
                        ),
                        ButtonSegment(
                          value: 'DELIVERY',
                          label: Text('Delivery'),
                          icon: Icon(Icons.local_shipping_outlined),
                        ),
                      ],
                      selected: {fulfillmentType},
                      onSelectionChanged: (values) => setState(() {
                        fulfillmentType = values.first;
                        message = '';
                        if (fulfillmentType == 'PICKUP') {
                          for (final key in shippingDetails.keys.toList()) {
                            shippingDetails[key] = '';
                          }
                        }
                      }),
                    ),
                    if (fulfillmentType == 'DELIVERY') ...[
                      const SizedBox(height: AppSpacing.sm),
                      const Text(
                        'Delivery sin costo adicional. La sucursal seleccionada prepara el inventario.',
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      _shippingField(
                        'recipient_name',
                        'Nombre del destinatario',
                        Icons.person_outline,
                      ),
                      _shippingField(
                        'recipient_ci',
                        'CI',
                        Icons.badge_outlined,
                      ),
                      _shippingField(
                        'recipient_phone',
                        'Teléfono',
                        Icons.phone_outlined,
                      ),
                      _shippingField(
                        'department_or_city',
                        'Departamento/Ciudad',
                        Icons.location_city_outlined,
                      ),
                      _shippingField('zone', 'Zona', Icons.map_outlined),
                      _shippingField(
                        'street',
                        'Calle',
                        Icons.signpost_outlined,
                      ),
                      _shippingField(
                        'house_number',
                        'Número de casa',
                        Icons.home_outlined,
                      ),
                      _shippingField(
                        'reference',
                        'Referencia',
                        Icons.notes_outlined,
                      ),
                    ],
                    const SizedBox(height: AppSpacing.md),
                    DropdownButtonFormField<String>(
                      initialValue: selectedPaymentMethod,
                      decoration: const InputDecoration(
                        labelText: 'Método de pago',
                        prefixIcon: Icon(Icons.payment_outlined),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'CARD',
                          child: Text('Tarjeta de Crédito / Débito'),
                        ),
                        DropdownMenuItem(
                          value: 'QR',
                          child: Text('Pago QR Simple (Bolivia)'),
                        ),
                        DropdownMenuItem(
                          value: 'TRANSFER',
                          child: Text('Transferencia Bancaria'),
                        ),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setState(() {
                            selectedPaymentMethod = val;
                            message = '';
                            if (val != 'QR') qrPayment = null;
                          });
                          if (val == 'QR') prepareQrPayment();
                        }
                      },
                    ),
                    if (selectedPaymentMethod == 'CARD') ...[
                      const SizedBox(height: AppSpacing.md),
                      _cardPaymentPanel(context),
                    ],
                    if (selectedPaymentMethod == 'QR') ...[
                      const SizedBox(height: AppSpacing.md),
                      if (loadingQr)
                        const Center(child: CircularProgressIndicator())
                      else if (qrPayment != null) ...[
                        Center(
                          child: Image.network(
                            qrPayment!['qr_image_url'] as String,
                            width: 230,
                            height: 230,
                            errorBuilder: (_, _, _) =>
                                const Icon(Icons.qr_code_2, size: 180),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        Center(
                          child: Text(
                            'Escaneá el código desde tu banca móvil y luego confirmá la transferencia.',
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    ],
                    const SizedBox(height: AppSpacing.md),
                    FilledButton(
                      onPressed:
                          paying ||
                              loadingQr ||
                              (selectedPaymentMethod == 'QR' &&
                                  qrPayment == null)
                          ? null
                          : checkout,
                      child: Text(
                        paying
                            ? 'Procesando...'
                            : selectedPaymentMethod == 'QR'
                            ? 'Confirmar pago QR'
                            : PaymentConfig.isStripeConfigured
                            ? 'Pagar con tarjeta'
                            : 'Pagar con tarjeta (modo local)',
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    OutlinedButton(
                      onPressed: paying || selectedPaymentMethod == 'QR'
                          ? null
                          : demoCheckout,
                      child: const Text('Pago electrónico alternativo'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _shippingField(String key, String label, IconData icon) => Padding(
    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
    child: TextFormField(
      initialValue: shippingDetails[key],
      decoration: InputDecoration(labelText: label, prefixIcon: Icon(icon)),
      onChanged: (value) => shippingDetails[key] = value,
    ),
  );

  Widget _confirmationState(BuildContext context) {
    final order = RegExp(
      r'FS-[A-Z0-9-]+',
      caseSensitive: false,
    ).firstMatch(message)?.group(0)?.toUpperCase();
    final isQr = message.toLowerCase().contains('qr');
    final fulfillment = message.toLowerCase().contains('delivery')
        ? 'Delivery solicitado'
        : 'Retiro en sucursal';

    return Container(
      margin: const EdgeInsets.only(top: AppSpacing.md),
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.charcoal, AppColors.goldDeep],
        ),
        borderRadius: BorderRadius.circular(AppRadii.xl),
        boxShadow: [
          BoxShadow(
            color: AppColors.goldDeep.withValues(alpha: .22),
            blurRadius: 24,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 58,
                height: 58,
                decoration: const BoxDecoration(
                  color: AppColors.ivory,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.check_rounded,
                  color: AppColors.goldDeep,
                  size: 34,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'PAGO APROBADO',
                      style: TextStyle(
                        color: AppColors.ivory,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.8,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Gracias por elegirnos',
                      style: TextStyle(
                        color: AppColors.ivory,
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xl),
          const Text(
            'Tu compra fue registrada y ya podemos preparar tu pedido.',
            style: TextStyle(color: AppColors.ivory, height: 1.45),
          ),
          const SizedBox(height: AppSpacing.lg),
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: AppColors.ivory.withValues(alpha: .12),
              borderRadius: BorderRadius.circular(AppRadii.md),
              border: Border.all(color: AppColors.ivory.withValues(alpha: .22)),
            ),
            child: Column(
              children: [
                _confirmationRow('Pedido', order ?? 'Confirmado'),
                const Divider(color: Colors.white24, height: 20),
                _confirmationRow('Pago', isQr ? 'Código QR' : 'Tarjeta'),
                const Divider(color: Colors.white24, height: 20),
                _confirmationRow('Entrega', fulfillment),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Icons.arrow_back),
              label: const Text('Volver al catálogo'),
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.ivory,
                foregroundColor: AppColors.charcoal,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _confirmationRow(String label, String value) => Row(
    mainAxisAlignment: MainAxisAlignment.spaceBetween,
    children: [
      Text(label, style: const TextStyle(color: Colors.white70)),
      Flexible(
        child: Text(
          value,
          textAlign: TextAlign.right,
          style: const TextStyle(
            color: AppColors.ivory,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
    ],
  );

  Widget _cardPaymentPanel(BuildContext context) => Container(
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: AppColors.parchment,
      borderRadius: BorderRadius.circular(AppRadii.md),
      border: Border.all(color: AppColors.goldDeep.withValues(alpha: .35)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: const BoxDecoration(
                color: AppColors.ivoryDeep,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.credit_card, color: AppColors.goldDeep),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    PaymentConfig.isStripeConfigured
                        ? 'Datos de la tarjeta'
                        : 'Pago con tarjeta',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    PaymentConfig.isStripeConfigured
                        ? 'Procesamiento seguro con Stripe'
                        : 'Respaldo electrónico para esta instalación',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.charcoalMuted,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.md),
        if (PaymentConfig.isStripeConfigured) ...[
          StatusPill(label: 'Stripe seguro activo', tone: StatusTone.success),
          const SizedBox(height: AppSpacing.sm),
          CardField(
            controller: cardController,
            countryCode: 'BO',
            enablePostalCode: false,
            decoration: InputDecoration(
              filled: true,
              fillColor: AppColors.parchment,
              hintText: 'Número de tarjeta    MM/AA    CVC',
              hintStyle: TextStyle(color: AppColors.charcoalMuted),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadii.md),
                borderSide: BorderSide(color: AppColors.ivoryDeep),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadii.md),
                borderSide: BorderSide(color: AppColors.ivoryDeep),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppRadii.md),
                borderSide: BorderSide(color: AppColors.goldDeep, width: 2),
              ),
            ),
            style: const TextStyle(color: AppColors.charcoal, fontSize: 16),
            numberHintText: 'Número de tarjeta',
            expirationHintText: 'MM/AA',
            cvcHintText: 'CVC',
            onCardChanged: (details) {
              final complete = details?.complete ?? false;
              if (cardComplete != complete && mounted) {
                setState(() => cardComplete = complete);
              }
            },
          ),
        ] else ...[
          StatusPill(label: 'Modo local disponible', tone: StatusTone.warning),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Esta APK no incluye una clave pública de Stripe. El pedido se procesará mediante el respaldo electrónico local, sin solicitar datos bancarios reales.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppColors.charcoalMuted,
              height: 1.45,
            ),
          ),
        ],
      ],
    ),
  );

  Widget _item(Map<String, dynamic> item) => Card(
    child: ListTile(
      minVerticalPadding: 16,
      title: Text(item['product_name'] as String),
      subtitle: Text(
        '${item['size_name']} · ${item['color_name']}\nCantidad: ${item['quantity']}',
      ),
      trailing: IconButton(
        onPressed: () => remove(item['id'] as int),
        icon: const Icon(Icons.delete_outline),
        tooltip: 'Quitar',
      ),
    ),
  );
}
