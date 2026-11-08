import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/offline/connectivity_monitor.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/fashion_ui.dart';
import '../data/exchange_models.dart';

class _PendingExchangeRetry {
  const _PendingExchangeRetry({
    required this.saleId,
    required this.request,
  });

  final int saleId;
  final ExchangeFinalizeRequest request;
}

class GarmentExchangeScreen extends ConsumerStatefulWidget {
  const GarmentExchangeScreen({super.key});

  @override
  ConsumerState<GarmentExchangeScreen> createState() =>
      _GarmentExchangeScreenState();
}

class _GarmentExchangeScreenState extends ConsumerState<GarmentExchangeScreen> {
  final TextEditingController _orderController = TextEditingController();
  final TextEditingController _returnedQtyController =
      TextEditingController(text: '1');
  final TextEditingController _newQtyController =
      TextEditingController(text: '1');
  final TextEditingController _cashTenderedController = TextEditingController();
  final TextEditingController _reasonController = TextEditingController();

  bool _loadingLookup = false;
  bool _loadingQuote = false;
  bool _submitting = false;

  String? _errorMessage;
  ExchangeLookupResult? _sale;
  List<ExchangeReplacementOption> _branchVariants = const [];

  int? _returnedVariantId;
  int? _newVariantId;
  bool _cashierConfirmed = false;

  ExchangeQuote? _quote;
  _PendingExchangeRetry? _pendingRetry;
  ExchangeReceipt? _receipt;

  @override
  void dispose() {
    _orderController.dispose();
    _returnedQtyController.dispose();
    _newQtyController.dispose();
    _cashTenderedController.dispose();
    _reasonController.dispose();
    super.dispose();
  }

  String _generateIdempotencyKey() {
    final random = Random.secure();
    final suffix = List<int>.generate(8, (_) => random.nextInt(16))
        .map((n) => n.toRadixString(16))
        .join();
    return 'mob-exch-${DateTime.now().microsecondsSinceEpoch}-$suffix';
  }

  String _formatMoney(double value) => value.toStringAsFixed(2);

  ExchangeLookupItem? get _selectedReturnedLine {
    final sale = _sale;
    final id = _returnedVariantId;
    if (sale == null || id == null) return null;
    for (final item in sale.items) {
      if (item.variantId == id) return item;
    }
    return null;
  }

  ExchangeReplacementOption? get _selectedReplacementOption {
    final id = _newVariantId;
    if (id == null) return null;
    for (final option in _branchVariants) {
      if (option.variantId == id) return option;
    }
    return null;
  }

  void _clearActiveQuote() {
    if (_pendingRetry != null) return;
    _quote = null;
    _cashTenderedController.clear();
    _cashierConfirmed = false;
  }

  void _resetAll() {
    setState(() {
      _orderController.clear();
      _returnedQtyController.text = '1';
      _newQtyController.text = '1';
      _cashTenderedController.clear();
      _reasonController.clear();
      _errorMessage = null;
      _sale = null;
      _branchVariants = const [];
      _returnedVariantId = null;
      _newVariantId = null;
      _cashierConfirmed = false;
      _quote = null;
      _pendingRetry = null;
      _receipt = null;
    });
  }

  Future<void> _lookupSale(bool isOffline) async {
    if (isOffline || _pendingRetry != null) {
      setState(() {
        _errorMessage =
            'El cambio de prendas requiere conexión activa con el servidor.';
      });
      return;
    }
    final cleanOrder = _orderController.text.trim();
    if (cleanOrder.isEmpty) {
      setState(() {
        _errorMessage = 'Ingresá el número de orden o recibo para buscar.';
      });
      return;
    }

    setState(() {
      _loadingLookup = true;
      _errorMessage = null;
      _quote = null;
      _receipt = null;
    });

    try {
      final repo = ref.read(exchangeRepositoryProvider);
      final sale = await repo.lookupSale(cleanOrder);
      final variants = await repo.fetchBranchVariants(sale.branchId);
      final sellableVariants =
          variants.where((v) => v.availableQuantity > 0).toList();
      final firstEligibleLine = sale.items
          .where((item) => item.remainingExchangeableQuantity > 0)
          .firstOrNull;

      if (!mounted) return;
      setState(() {
        _sale = sale;
        _branchVariants = sellableVariants;
        _returnedVariantId = firstEligibleLine?.variantId;
        _returnedQtyController.text = '1';
        _newVariantId = sellableVariants.firstOrNull?.variantId;
        _newQtyController.text = '1';
        _cashTenderedController.clear();
        _cashierConfirmed = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'No se pudo consultar la venta: $e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _loadingLookup = false;
        });
      }
    }
  }

  Future<void> _requestQuote(bool isOffline) async {
    if (isOffline || _pendingRetry != null) {
      setState(() {
        _errorMessage =
            'El cambio de prendas requiere conexión activa con el servidor.';
      });
      return;
    }
    final sale = _sale;
    final returnedLine = _selectedReturnedLine;
    final replacement = _selectedReplacementOption;
    if (sale == null || returnedLine == null || replacement == null) {
      setState(() {
        _errorMessage =
            'Seleccioná la prenda devuelta y la variante de reemplazo.';
      });
      return;
    }

    final returnedQty = int.tryParse(_returnedQtyController.text.trim()) ?? 0;
    final newQty = int.tryParse(_newQtyController.text.trim()) ?? 0;
    if (returnedQty < 1 ||
        returnedQty > returnedLine.remainingExchangeableQuantity) {
      setState(() {
        _errorMessage =
            'La cantidad a devolver debe estar entre 1 y ${returnedLine.remainingExchangeableQuantity}.';
      });
      return;
    }
    if (newQty < 1 || newQty > replacement.availableQuantity) {
      setState(() {
        _errorMessage =
            'La cantidad de reemplazo debe estar entre 1 y ${replacement.availableQuantity}.';
      });
      return;
    }

    setState(() {
      _loadingQuote = true;
      _errorMessage = null;
      _receipt = null;
    });

    try {
      final repo = ref.read(exchangeRepositoryProvider);
      final quote = await repo.requestQuote(
        sale.saleId,
        ExchangeQuoteRequest(
          returnedVariantId: returnedLine.variantId,
          returnedQuantity: returnedQty,
          newVariantId: replacement.variantId,
          newQuantity: newQty,
        ),
      );
      if (!mounted) return;
      setState(() {
        _quote = quote;
        _cashTenderedController.clear();
        _cashierConfirmed = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'No se pudo obtener la cotización: $e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _loadingQuote = false;
        });
      }
    }
  }

  Future<void> _finalizeExchange(bool isOffline) async {
    if (isOffline) {
      setState(() {
        _errorMessage =
            'Sin conexión: no confirmes ni entregues la prenda sin respuesta del servidor.';
      });
      return;
    }

    final pending = _pendingRetry;
    if (pending != null) {
      await _submitFinalize(pending.saleId, pending.request);
      return;
    }

    final sale = _sale;
    final quote = _quote;
    if (sale == null || quote == null) {
      setState(() {
        _errorMessage = 'Solicitá una cotización vigente antes de confirmar.';
      });
      return;
    }

    if (quote.difference != 0 && !quote.cashSettlementEligible) {
      setState(() {
        _errorMessage =
            'La venta original no fue liquidada íntegramente en efectivo; no se permiten diferencias de precio.';
      });
      return;
    }

    String? formattedCashTendered;
    if (quote.difference > 0) {
      final raw = _cashTenderedController.text.trim().replaceAll(',', '.');
      final parsed = double.tryParse(raw);
      if (parsed == null || parsed + 1e-9 < quote.difference) {
        setState(() {
          _errorMessage =
              'Ingresá un monto en efectivo igual o mayor a Bs. ${_formatMoney(quote.difference)}.';
        });
        return;
      }
      formattedCashTendered = parsed.toStringAsFixed(2);
    } else if (quote.difference < 0 && !_cashierConfirmed) {
      setState(() {
        _errorMessage =
            'Confirmá explícitamente la devolución en efectivo al cliente antes de finalizar.';
      });
      return;
    }

    final request = ExchangeFinalizeRequest(
      returnedVariantId: quote.returnedVariantId,
      returnedQuantity: quote.returnedQuantity,
      newVariantId: quote.newVariantId,
      newQuantity: quote.newQuantity,
      quoteFingerprint: quote.quoteFingerprint,
      quoteExpiresAt: quote.expiresAt,
      idempotencyKey: _generateIdempotencyKey(),
      cashTendered: formattedCashTendered,
      cashierConfirmed: quote.difference < 0 ? _cashierConfirmed : false,
      reason: _reasonController.text.trim().isEmpty
          ? null
          : _reasonController.text.trim(),
    );

    await _submitFinalize(sale.saleId, request);
  }

  Future<void> _submitFinalize(
    int saleId,
    ExchangeFinalizeRequest request,
  ) async {
    setState(() {
      _submitting = true;
      _errorMessage = null;
    });

    try {
      final repo = ref.read(exchangeRepositoryProvider);
      final receipt = await repo.finalizeExchange(saleId, request);
      if (!mounted) return;
      setState(() {
        _receipt = receipt;
        _pendingRetry = null;
        _quote = null;
        _cashTenderedController.clear();
        _cashierConfirmed = false;
        final currentSale = _sale;
        if (currentSale != null) {
          final updatedItems = currentSale.items.map((item) {
            if (item.variantId == receipt.returnedVariantId) {
              final nextRemaining = max(
                0,
                item.remainingExchangeableQuantity - receipt.returnedQuantity,
              );
              return item.copyWith(
                remainingExchangeableQuantity: nextRemaining,
              );
            }
            return item;
          }).toList();
          _sale = currentSale.copyWith(items: updatedItems);
          final nextEligible = updatedItems
              .where((item) => item.remainingExchangeableQuantity > 0)
              .firstOrNull;
          _returnedVariantId = nextEligible?.variantId;
        }
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      final isAmbiguous = e.statusCode == 0 || e.statusCode >= 500;
      setState(() {
        _errorMessage = e.message;
        if (isAmbiguous) {
          _pendingRetry = _PendingExchangeRetry(
            saleId: saleId,
            request: request,
          );
        } else {
          _pendingRetry = null;
          if (e.statusCode == 409) {
            _quote = null;
          }
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage =
            'Respuesta incierta del servidor ($e). Reintentá antes de entregar la prenda.';
        _pendingRetry = _PendingExchangeRetry(
          saleId: saleId,
          request: request,
        );
      });
    } finally {
      if (mounted) {
        setState(() {
          _submitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final connectivity = ref.watch(connectivityMonitorProvider);
    final isOffline = connectivity.status == ConnectivityStatus.offline;
    final controlsFrozen =
        isOffline || _pendingRetry != null || _submitting || _loadingLookup;
    final quote = _quote;
    final sale = _sale;
    final receipt = _receipt;
    final nonEligibleDifference =
        quote != null && quote.difference != 0 && !quote.cashSettlementEligible;

    final parsedTender = double.tryParse(
      _cashTenderedController.text.trim().replaceAll(',', '.'),
    );
    final estimatedChange =
        (quote != null &&
            quote.difference > 0 &&
            parsedTender != null &&
            parsedTender >= quote.difference)
        ? parsedTender - quote.difference
        : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CAMBIO DE PRENDA (POS)'),
        actions: [
          IconButton(
            key: const Key('exchange_reset_btn'),
            onPressed: _submitting ? null : _resetAll,
            icon: const Icon(Icons.refresh),
            tooltip: 'Nuevo cambio',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const FashionSectionHeader(
              eyebrow: 'Punto de Venta · Cambios',
              title: 'Cambio de prenda en línea',
              body:
                  'Buscá el comprobante original, cotizá la diferencia con precios del servidor y confirmá antes de entregar el reemplazo.',
            ),
            const SizedBox(height: AppSpacing.md),
            if (isOffline) ...[
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: AppColors.rose.withValues(alpha: .14),
                  borderRadius: BorderRadius.circular(AppRadii.md),
                  border: Border.all(color: AppColors.rose),
                ),
                child: const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.wifi_off, color: AppColors.rose),
                    SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        'Operación exclusiva en línea: no entregues la prenda de reemplazo sin confirmación del servidor. Esta operación nunca se encola en la bandeja offline.',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.md),
            ],
            if (_pendingRetry != null) ...[
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: AppColors.goldDeep.withValues(alpha: .14),
                  borderRadius: BorderRadius.circular(AppRadii.md),
                  border: Border.all(color: AppColors.goldDeep),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Respuesta incierta del servidor. Los controles quedaron bloqueados para evitar duplicados: reintentá con la misma clave de idempotencia antes de entregar la prenda.',
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    FilledButton.icon(
                      key: const Key('exchange_retry_btn'),
                      onPressed: (isOffline || _submitting)
                          ? null
                          : () => _finalizeExchange(isOffline),
                      icon: const Icon(Icons.replay),
                      label: Text(
                        _submitting
                            ? 'Reintentando...'
                            : 'Reintentar confirmación',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.md),
            ],
            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: AppColors.rose.withValues(alpha: .1),
                  borderRadius: BorderRadius.circular(AppRadii.md),
                  border: Border.all(color: AppColors.rose),
                ),
                child: Text(
                  _errorMessage!,
                  style: const TextStyle(color: AppColors.rose),
                ),
              ),
              const SizedBox(height: AppSpacing.md),
            ],
            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      '1. Buscar venta original',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    TextField(
                      key: const Key('exchange_order_input'),
                      controller: _orderController,
                      enabled: !controlsFrozen,
                      textInputAction: TextInputAction.search,
                      decoration: const InputDecoration(
                        labelText: 'Número de orden / recibo',
                        hintText: 'Ingresa el código exacto del comprobante',
                      ),
                      onSubmitted: (_) => _lookupSale(isOffline),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    FilledButton.icon(
                      key: const Key('exchange_lookup_btn'),
                      onPressed: controlsFrozen
                          ? null
                          : () => _lookupSale(isOffline),
                      icon: const Icon(Icons.search),
                      label: Text(
                        _loadingLookup ? 'Buscando...' : 'Buscar venta',
                      ),
                    ),
                  ],
                ),
              ),
            ),
            if (sale != null) ...[
              const SizedBox(height: AppSpacing.md),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '2. Venta ${sale.orderNumber}',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ),
                          StatusPill(
                            label: sale.status,
                            tone: StatusTone.success,
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        'Sucursal #${sale.branchId} · Fecha: ${sale.saleDate}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const Divider(height: AppSpacing.lg),
                      for (final line in sale.items)
                        Padding(
                          padding: const EdgeInsets.only(bottom: AppSpacing.xs),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  '${line.name} · SKU ${line.sku}\nPagado neto: Bs. ${_formatMoney(line.netPaidLineTotal)} (${line.purchasedQuantity} u.)',
                                ),
                              ),
                              StatusPill(
                                label:
                                    'Restantes: ${line.remainingExchangeableQuantity}',
                                tone: line.remainingExchangeableQuantity > 0
                                    ? StatusTone.neutral
                                    : StatusTone.warning,
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: AppSpacing.md),
                      DropdownButtonFormField<int>(
                        key: const Key('exchange_returned_variant_dropdown'),
                        initialValue: _returnedVariantId,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Prenda devuelta por el cliente',
                        ),
                        items: sale.items
                            .where(
                              (item) => item.remainingExchangeableQuantity > 0,
                            )
                            .map(
                              (item) => DropdownMenuItem<int>(
                                value: item.variantId,
                                child: Text(
                                  '${item.name} (disp. cambio: ${item.remainingExchangeableQuantity})',
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            )
                            .toList(),
                        onChanged: controlsFrozen
                            ? null
                            : (next) {
                                setState(() {
                                  _returnedVariantId = next;
                                  _clearActiveQuote();
                                });
                              },
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      TextField(
                        key: const Key('exchange_returned_qty_input'),
                        controller: _returnedQtyController,
                        enabled: !controlsFrozen,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Cantidad a recibir',
                        ),
                        onChanged: (_) => setState(_clearActiveQuote),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      DropdownButtonFormField<int>(
                        key: const Key('exchange_new_variant_dropdown'),
                        initialValue: _newVariantId,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Variante de reemplazo (misma sucursal)',
                        ),
                        items: _branchVariants
                            .map(
                              (option) => DropdownMenuItem<int>(
                                value: option.variantId,
                                child: Text(
                                  option.displayLabel,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            )
                            .toList(),
                        onChanged: controlsFrozen
                            ? null
                            : (next) {
                                setState(() {
                                  _newVariantId = next;
                                  _clearActiveQuote();
                                });
                              },
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      TextField(
                        key: const Key('exchange_new_qty_input'),
                        controller: _newQtyController,
                        enabled: !controlsFrozen,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Cantidad a entregar',
                        ),
                        onChanged: (_) => setState(_clearActiveQuote),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      OutlinedButton.icon(
                        key: const Key('exchange_quote_btn'),
                        onPressed:
                            (controlsFrozen ||
                                _loadingQuote ||
                                _returnedVariantId == null ||
                                _newVariantId == null)
                            ? null
                            : () => _requestQuote(isOffline),
                        icon: const Icon(Icons.calculate_outlined),
                        label: Text(
                          _loadingQuote
                              ? 'Cotizando...'
                              : 'Cotizar cambio en servidor',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            if (quote != null) ...[
              const SizedBox(height: AppSpacing.md),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        '3. Cotización y liquidación en caja',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'Valor reconocido: Bs. ${_formatMoney(quote.returnedValue)}',
                      ),
                      Text(
                        'Valor nueva prenda: Bs. ${_formatMoney(quote.deliveredValue)} (unit. Bs. ${_formatMoney(quote.replacementUnitPrice)})',
                      ),
                      Text(
                        'Stock disponible en sucursal: ${quote.availableStock}',
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        quote.difference > 0
                            ? 'Diferencia a cobrar en efectivo: Bs. ${_formatMoney(quote.difference)}'
                            : quote.difference < 0
                            ? 'Diferencia a devolver en efectivo: Bs. ${_formatMoney(-quote.difference)}'
                            : 'Sin diferencia monetaria (Bs. 0.00)',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      if (nonEligibleDifference) ...[
                        Container(
                          padding: const EdgeInsets.all(AppSpacing.sm),
                          decoration: BoxDecoration(
                            color: AppColors.rose.withValues(alpha: .12),
                            borderRadius: BorderRadius.circular(AppRadii.sm),
                            border: Border.all(color: AppColors.rose),
                          ),
                          child: const Text(
                            'La venta original no fue liquidada íntegramente en efectivo; no se permiten diferencias de precio en esta versión.',
                          ),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                      ],
                      if (quote.difference > 0 &&
                          quote.cashSettlementEligible) ...[
                        TextField(
                          key: const Key('exchange_cash_tendered_input'),
                          controller: _cashTenderedController,
                          enabled: !controlsFrozen,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: const InputDecoration(
                            labelText: 'Efectivo recibido (Bs.)',
                          ),
                          onChanged: (_) => setState(() {}),
                        ),
                        if (estimatedChange != null) ...[
                          const SizedBox(height: AppSpacing.xs),
                          Text(
                            'Vuelto estimado: Bs. ${_formatMoney(estimatedChange)}',
                          ),
                        ],
                        const SizedBox(height: AppSpacing.sm),
                      ],
                      if (quote.difference < 0 &&
                          quote.cashSettlementEligible) ...[
                        CheckboxListTile(
                          key: const Key('exchange_cashier_confirmed_checkbox'),
                          contentPadding: EdgeInsets.zero,
                          value: _cashierConfirmed,
                          onChanged: controlsFrozen
                              ? null
                              : (checked) {
                                  setState(() {
                                    _cashierConfirmed = checked ?? false;
                                  });
                                },
                          title: Text(
                            'Confirmo devolución en efectivo al cliente por Bs. ${_formatMoney(-quote.difference)}',
                          ),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                      ],
                      TextField(
                        key: const Key('exchange_reason_input'),
                        controller: _reasonController,
                        enabled: !controlsFrozen,
                        decoration: const InputDecoration(
                          labelText: 'Motivo / observación (opcional)',
                        ),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      FilledButton.icon(
                        key: const Key('exchange_finalize_btn'),
                        onPressed: (controlsFrozen || nonEligibleDifference)
                            ? null
                            : () => _finalizeExchange(isOffline),
                        icon: const Icon(Icons.verified_outlined),
                        label: Text(
                          _submitting
                              ? 'Confirmando...'
                              : 'Confirmar cambio en servidor',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            if (receipt != null) ...[
              const SizedBox(height: AppSpacing.md),
              Card(
                key: const Key('exchange_receipt_card'),
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Comprobante de cambio confirmado',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                          ),
                          StatusPill(
                            label: receipt.status,
                            tone: StatusTone.success,
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Text('Orden: ${receipt.orderNumber}'),
                      Text(
                        'Valor reconocido: Bs. ${_formatMoney(receipt.returnedValue)} · Valor entregado: Bs. ${_formatMoney(receipt.deliveredValue)}',
                      ),
                      Text(
                        'Diferencia: Bs. ${_formatMoney(receipt.difference)}',
                      ),
                      if (receipt.cashTendered != null)
                        Text(
                          'Efectivo recibido: Bs. ${_formatMoney(receipt.cashTendered!)} · Vuelto: Bs. ${_formatMoney(receipt.cashChange ?? 0)}',
                        ),
                      if (receipt.cashRefunded != null)
                        Text(
                          'Reembolso en efectivo entregado: Bs. ${_formatMoney(receipt.cashRefunded!)}',
                        ),
                      const Divider(height: AppSpacing.lg),
                      Row(
                        children: [
                          const Icon(
                            Icons.inventory_2_outlined,
                            color: AppColors.goldDeep,
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Text(
                              'Cuarentena #${receipt.quarantineId ?? '-'} (${receipt.quarantineStatus ?? 'PENDING'}): la prenda devuelta ingresó a cuarentena pendiente de inspección y aún no suma al stock vendible.',
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
