import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/offline/offline_models.dart';
import '../../../core/providers.dart';

class OfflineOperationsScreen extends ConsumerStatefulWidget {
  const OfflineOperationsScreen({super.key});

  @override
  ConsumerState<OfflineOperationsScreen> createState() =>
      _OfflineOperationsScreenState();
}

class _OfflineOperationsScreenState
    extends ConsumerState<OfflineOperationsScreen> {
  String _activeFilter = 'ALL'; // 'ALL', 'PENDING_SYNC', 'CONFIRMED', 'CONFLICT'
  List<OfflineOperationRecord> _operations = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadOperations();
  }

  Future<void> _loadOperations() async {
    setState(() => _loading = true);
    final repo = ref.read(offlineTransactionRepositoryProvider);
    final filter = _activeFilter == 'ALL' ? null : _activeFilter;
    final items = await repo.listOperations(status: filter);
    if (!mounted) return;
    setState(() {
      _operations = items;
      _loading = false;
    });
    ref.read(syncTransactionServiceProvider).refreshPendingCount();
  }

  Future<void> _triggerSync() async {
    final syncService = ref.read(syncTransactionServiceProvider);
    final result = await syncService.syncPendingTransactions();
    if (!mounted) return;

    if (result != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Sincronización finalizada: ${result.confirmedCount} confirmadas, ${result.conflictCount} con conflicto.',
          ),
          backgroundColor: const Color(0xFF0F766E),
        ),
      );
    } else if (syncService.syncError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al sincronizar: ${syncService.syncError}'),
          backgroundColor: Colors.redAccent,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No hay operaciones pendientes de sincronización.'),
        ),
      );
    }

    await _loadOperations();
  }

  @override
  Widget build(BuildContext context) {
    final syncService = ref.watch(syncTransactionServiceProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Bandeja Offline'),
        actions: [
          IconButton(
            icon: const Icon(Icons.people_alt_outlined),
            tooltip: 'Clientes Offline',
            onPressed: _showOfflineCustomersSheet,
          ),
          if (syncService.isSyncing)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.sync),
              tooltip: 'Sincronizar ahora',
              onPressed: _triggerSync,
            ),
        ],
      ),
      body: Column(
        children: [
          _filterBar(),
          if (syncService.syncError != null)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF2F2),
                border: Border.all(color: const Color(0xFFF87171)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const Icon(Icons.error_outline,
                      color: Color(0xFFB91C1C), size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      syncService.syncError!,
                      style: const TextStyle(
                          color: Color(0xFF7F1D1D), fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _operations.isEmpty
                    ? _emptyState()
                    : RefreshIndicator(
                        onRefresh: _loadOperations,
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _operations.length,
                          itemBuilder: (context, index) =>
                              _operationCard(_operations[index]),
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _filterBar() {
    final filters = [
      {'key': 'ALL', 'label': 'Todas'},
      {'key': 'PENDING_SYNC', 'label': 'Pendientes'},
      {'key': 'CONFIRMED', 'label': 'Confirmadas'},
      {'key': 'CONFLICT', 'label': 'Conflictos'},
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Row(
        children: filters.map((f) {
          final isSelected = _activeFilter == f['key'];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(f['label']!),
              selected: isSelected,
              onSelected: (selected) {
                if (selected) {
                  setState(() => _activeFilter = f['key']!);
                  _loadOperations();
                }
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox_outlined, size: 56, color: Colors.grey.shade400),
          const SizedBox(height: 12),
          const Text(
            'Sin operaciones registradas',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Text(
            'No hay transacciones offline bajo este filtro.',
            style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
          ),
        ],
      ),
    );
  }

  Widget _operationCard(OfflineOperationRecord op) {
    Color statusColor;
    Color statusBg;
    IconData statusIcon;
    String statusLabel;

    switch (op.status) {
      case 'CONFIRMED':
        statusColor = const Color(0xFF047857);
        statusBg = const Color(0xFFD1FAE5);
        statusIcon = Icons.check_circle_outline;
        statusLabel = 'CONFIRMADA';
        break;
      case 'CONFLICT':
        statusColor = const Color(0xFFB91C1C);
        statusBg = const Color(0xFFFEE2E2);
        statusIcon = Icons.warning_amber_rounded;
        statusLabel = 'CONFLICTO';
        break;
      case 'PENDING_SYNC':
      default:
        statusColor = const Color(0xFFB45309);
        statusBg = const Color(0xFFFEF3C7);
        statusIcon = Icons.schedule;
        statusLabel = 'PENDIENTE';
        break;
    }

    final isSale = op.operationType == 'SALE';
    Map<String, dynamic> payloadMap = {};
    try {
      payloadMap = jsonDecode(op.payloadJson) as Map<String, dynamic>;
    } catch (_) {}

    Map<String, dynamic>? conflictMap;
    if (op.conflictDetailJson != null) {
      try {
        conflictMap =
            jsonDecode(op.conflictDetailJson!) as Map<String, dynamic>;
      } catch (_) {}
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isSale
                        ? const Color(0xFFEFF6FF)
                        : const Color(0xFFF5F3FF),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    isSale ? 'Venta Contado' : 'Reserva Prenda',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: isSale
                          ? const Color(0xFF1D4ED8)
                          : const Color(0xFF6D28D9),
                    ),
                  ),
                ),
                const Spacer(),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    children: [
                      Icon(statusIcon, size: 12, color: statusColor),
                      const SizedBox(width: 4),
                      Text(
                        statusLabel,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: statusColor,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              op.clientOperationId,
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 11,
                color: Colors.grey.shade600,
              ),
            ),
            const SizedBox(height: 6),
            if (isSale) ...[
              Text(
                'Total: \$${payloadMap['total'] ?? '0.00'}',
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (payloadMap['customer_name'] != null &&
                  (payloadMap['customer_name'] as String).trim().isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 2),
                  child: Text(
                    'Cliente: ${payloadMap['customer_name']}${payloadMap['customer_nit'] != null ? ' (CI/NIT: ${payloadMap['customer_nit']})' : ''}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              Text(
                'Prendas: ${(payloadMap['items'] as List?)?.length ?? 0}',
                style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
              ),
            ] else ...[
              Text(
                'Cliente: ${payloadMap['customer_name'] ?? 'Sin nombre'}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (payloadMap['customer_nit'] != null ||
                  payloadMap['customer_phone'] != null)
                Text(
                  [
                    if (payloadMap['customer_nit'] != null)
                      'CI/NIT: ${payloadMap['customer_nit']}',
                    if (payloadMap['customer_phone'] != null)
                      'Tel: ${payloadMap['customer_phone']}',
                  ].join(' · '),
                  style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                ),
              Text(
                'Prendas reservadas: ${(payloadMap['items'] as List?)?.length ?? 0}',
                style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
              ),
            ],
            if (op.orderNumber != null) ...[
              const SizedBox(height: 4),
              Text(
                'Orden confirmada: ${op.orderNumber}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF047857),
                ),
              ),
            ],
            if (op.reservationId != null) ...[
              const SizedBox(height: 4),
              Text(
                'ID Reserva: ${op.reservationId}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF047857),
                ),
              ),
            ],
            if (conflictMap != null) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF2F2),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'Conflicto [${conflictMap['code']}]: ${conflictMap['message']}',
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFFB91C1C),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              'Registrada: ${op.createdAt}',
              style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showOfflineCustomersSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const _OfflineCustomersSheet(),
    );
  }
}

class _OfflineCustomersSheet extends ConsumerStatefulWidget {
  const _OfflineCustomersSheet();

  @override
  ConsumerState<_OfflineCustomersSheet> createState() =>
      _OfflineCustomersSheetState();
}

class _OfflineCustomersSheetState
    extends ConsumerState<_OfflineCustomersSheet> {
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _nitCtrl = TextEditingController();
  final TextEditingController _phoneCtrl = TextEditingController();
  final TextEditingController _searchCtrl = TextEditingController();
  List<OfflineCustomerRecord> _customers = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadCustomers();
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _nitCtrl.dispose();
    _phoneCtrl.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadCustomers([String? query]) async {
    setState(() => _loading = true);
    final repo = ref.read(offlineTransactionRepositoryProvider);
    final items = await repo.listCustomers(query: query ?? '');
    if (!mounted) return;
    setState(() {
      _customers = items;
      _loading = false;
    });
  }

  Future<void> _saveCustomer() async {
    final fullName = _nameCtrl.text.trim();
    if (fullName.isEmpty) return;
    final repo = ref.read(offlineTransactionRepositoryProvider);
    await repo.saveCustomer(
      fullName: fullName,
      nitCi: _nitCtrl.text.trim(),
      phone: _phoneCtrl.text.trim(),
    );
    _nameCtrl.clear();
    _nitCtrl.clear();
    _phoneCtrl.clear();
    await _loadCustomers(_searchCtrl.text.trim());
  }

  Future<void> _deleteCustomer(String customerId) async {
    final repo = ref.read(offlineTransactionRepositoryProvider);
    await repo.deleteCustomer(customerId);
    await _loadCustomers(_searchCtrl.text.trim());
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SizedBox(
        height: 460,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Clientes Offline',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            TextField(
              controller: _nameCtrl,
              decoration: const InputDecoration(
                labelText: 'Nombre o Razón Social',
                isDense: true,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _nitCtrl,
                    decoration: const InputDecoration(
                      labelText: 'CI / NIT',
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _phoneCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Teléfono',
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _saveCustomer,
                  child: const Text('Guardar'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _searchCtrl,
              decoration: const InputDecoration(
                hintText: 'Buscar por nombre, CI/NIT o teléfono...',
                prefixIcon: Icon(Icons.search, size: 18),
                isDense: true,
              ),
              onChanged: _loadCustomers,
            ),
            const SizedBox(height: 8),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _customers.isEmpty
                      ? const Center(
                          child: Text(
                            'Sin clientes registrados localmente.',
                            style: TextStyle(fontSize: 13, color: Colors.grey),
                          ),
                        )
                      : ListView.separated(
                          itemCount: _customers.length,
                          separatorBuilder: (_, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final c = _customers[index];
                            return ListTile(
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                              title: Text(
                                c.fullName,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600),
                              ),
                              subtitle: Text(
                                'CI/NIT: ${c.nitCi} · Tel: ${c.phone ?? '-'}',
                                style: const TextStyle(fontSize: 12),
                              ),
                              trailing: IconButton(
                                icon: const Icon(Icons.delete_outline,
                                    size: 18, color: Colors.redAccent),
                                onPressed: () => _deleteCustomer(c.id),
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}
