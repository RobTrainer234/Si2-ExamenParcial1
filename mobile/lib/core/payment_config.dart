enum PaymentProvider { stripe, sandboxDemo }

class PaymentConfig {
  static const provider = PaymentProvider.stripe;
  static const publishableKey = String.fromEnvironment(
    'STRIPE_PUBLISHABLE_KEY',
  );
  static const currency = String.fromEnvironment(
    'STRIPE_CURRENCY',
    defaultValue: 'USD',
  );

  static bool get isStripeConfigured => publishableKey.trim().isNotEmpty;
}
