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
  String message = '';

  @override
  void initState() {
    super.initState();
    load();
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
    if (PaymentConfig.provider != PaymentProvider.stripeTest) {
      await demoCheckout();
      return;
    }
    if (!PaymentConfig.isStripeConfigured) {
      setState(
        () => message =
            'Configurá STRIPE_PUBLISHABLE_KEY con --dart-define para usar Stripe test.',
      );
      return;
    }
    if (!_validateCheckout()) return;
    setState(() {
      paying = true;
      message = '';
    });
    try {
      Stripe.publishableKey = PaymentConfig.publishableKey;
      await Stripe.instance.applySettings();

      final sale = await ref
          .read(cartRepositoryProvider)
          .purchase(selectedBranchId!, fulfillmentType: fulfillmentType == 'DELIVERY' ? 'DELIVERY' : null, shippingDetails: fulfillmentType == 'DELIVERY' ? Map<String, dynamic>.from(shippingDetails) : null);
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

      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          paymentIntentClientSecret: clientSecret,
          merchantDisplayName: 'FashionStore',
          style: ThemeMode.system,
        ),
      );
      await Stripe.instance.presentPaymentSheet();
      final confirmed = await ref
          .read(cartRepositoryProvider)
          .confirmStripePayment(paymentIntentId);
      if (mounted) {
        setState(() {
          paying = false;
          message =
              'Compra ${confirmed['order_number'] ?? sale['order_number']} confirmada con Stripe test (${PaymentConfig.currency}). ${_fulfillmentSummary()}';
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
    } catch (_) {
      if (mounted) {
        setState(() {
          paying = false;
          message = 'No pudimos completar el pago Stripe test.';
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
          .purchase(selectedBranchId!, fulfillmentType: fulfillmentType == 'DELIVERY' ? 'DELIVERY' : null, shippingDetails: fulfillmentType == 'DELIVERY' ? Map<String, dynamic>.from(shippingDetails) : null);
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
          message =
              'Demostración ${sale['order_number']} confirmada (${_paymentLabel(selectedPaymentMethod)}). ${_fulfillmentSummary()}';
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
      setState(() => message = fulfillmentType == 'DELIVERY'
          ? 'Seleccioná la sucursal que preparará el delivery.'
          : 'Seleccioná la sucursal de retiro.');
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
      setState(() => message = 'Completá los datos de delivery: ${missing.join(', ')}.');
      return false;
    }
    return true;
  }

  String _fulfillmentSummary() {
    if (fulfillmentType != 'DELIVERY') return 'Retiro en sucursal seleccionada.';
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
                'Elegí retiro o delivery, mantené la sucursal como origen de inventario y pagá con Stripe test o sandbox.'
          ),
          const SizedBox(height: AppSpacing.lg),
          if (message.isNotEmpty) ...[
            FashionMessageCard(message: message, icon: Icons.info_outline),
            const SizedBox(height: AppSpacing.md),
          ],
          if (items.isEmpty)
            const FashionState(
              icon: Icons.shopping_bag_outlined,
              title: 'Tu carrito está vacío',
              message: 'Agregá una prenda desde el catálogo para continuar.',
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
                          ? 'Stripe test configurado'
                          : 'Stripe test requiere --dart-define',
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
                        onChanged: (val) =>
                            setState(() => selectedBranchId = val),
                      )
                    else
                      const Text(
                        'Cargando sucursales...',
                        style: TextStyle(color: Colors.grey, fontSize: 12),
                      ),
                    const SizedBox(height: AppSpacing.md),
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'PICKUP', label: Text('Retiro'), icon: Icon(Icons.storefront_outlined)),
                        ButtonSegment(value: 'DELIVERY', label: Text('Delivery'), icon: Icon(Icons.local_shipping_outlined)),
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
                      const Text('Delivery sin costo adicional. La sucursal seleccionada prepara el inventario.'),
                      const SizedBox(height: AppSpacing.sm),
                      _shippingField('recipient_name', 'Nombre del destinatario', Icons.person_outline),
                      _shippingField('recipient_ci', 'CI', Icons.badge_outlined),
                      _shippingField('recipient_phone', 'Teléfono', Icons.phone_outlined),
                      _shippingField('department_or_city', 'Departamento/Ciudad', Icons.location_city_outlined),
                      _shippingField('zone', 'Zona', Icons.map_outlined),
                      _shippingField('street', 'Calle', Icons.signpost_outlined),
                      _shippingField('house_number', 'Número de casa', Icons.home_outlined),
                      _shippingField('reference', 'Referencia', Icons.notes_outlined),
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
                          setState(() => selectedPaymentMethod = val);
                        }
                      },
                    ),
                    const SizedBox(height: AppSpacing.md),
                    FilledButton(
                      onPressed: paying ? null : checkout,
                      child: Text(
                        paying ? 'Procesando...' : 'Pagar con Stripe test',
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    OutlinedButton(
                      onPressed: paying ? null : demoCheckout,
                      child: const Text(
                        'Sandbox demo: pago electrónico simulado',
                      ),
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
