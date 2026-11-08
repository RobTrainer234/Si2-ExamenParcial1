import '../../../core/network/api_client.dart';
import 'exchange_models.dart';

class ExchangeRepository {
  ExchangeRepository(this._api);

  final ApiClient _api;

  Future<ExchangeLookupResult> lookupSale(String orderNumber) async {
    final cleanOrder = orderNumber.trim();
    final encoded = Uri.encodeComponent(cleanOrder);
    final response = await _api.get('/sales/lookup/$encoded');
    return ExchangeLookupResult.fromJson(
      Map<String, dynamic>.from(response as Map),
    );
  }

  Future<List<ExchangeReplacementOption>> fetchBranchVariants(
    int branchId,
  ) async {
    final response = await _api.get(
      '/inventory',
      query: {
        'branch_id': '$branchId',
        'page': '1',
        'page_size': '100',
      },
    );
    final data = Map<String, dynamic>.from(response as Map);
    final items = (data['items'] as List<dynamic>?) ?? const [];
    return items
        .map(
          (row) => ExchangeReplacementOption.fromJson(
            Map<String, dynamic>.from(row as Map),
          ),
        )
        .toList();
  }

  Future<ExchangeQuote> requestQuote(
    int saleId,
    ExchangeQuoteRequest request,
  ) async {
    final response = await _api.post(
      '/sales/$saleId/exchange/quote',
      body: request.toJson(),
    );
    return ExchangeQuote.fromJson(Map<String, dynamic>.from(response as Map));
  }

  Future<ExchangeReceipt> finalizeExchange(
    int saleId,
    ExchangeFinalizeRequest request,
  ) async {
    final response = await _api.post(
      '/sales/$saleId/exchange',
      body: request.toJson(),
    );
    return ExchangeReceipt.fromJson(Map<String, dynamic>.from(response as Map));
  }
}
