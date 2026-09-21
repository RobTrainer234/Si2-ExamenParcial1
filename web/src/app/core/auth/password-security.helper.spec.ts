import { FormControl } from '@angular/forms';
import { describe, expect, it } from 'vitest';
import {
  calculatePasswordStrength,
  evaluatePasswordRules,
  generateSecurePassword,
  isPasswordPolicyCompliant,
  passwordPolicyValidator,
} from './password-security.helper';

describe('password-security.helper', () => {
  it('correctly evaluates each password rule', () => {
    const rules = evaluatePasswordRules('Pass123!');
    expect(rules.find((r) => r.id === 'minLength')?.met).toBe(true);
    expect(rules.find((r) => r.id === 'upper')?.met).toBe(true);
    expect(rules.find((r) => r.id === 'lower')?.met).toBe(true);
    expect(rules.find((r) => r.id === 'number')?.met).toBe(true);
    expect(rules.find((r) => r.id === 'special')?.met).toBe(true);
  });

  it('flags unfulfilled rules when password is weak', () => {
    const rules = evaluatePasswordRules('abc');
    expect(rules.find((r) => r.id === 'minLength')?.met).toBe(false);
    expect(rules.find((r) => r.id === 'upper')?.met).toBe(false);
    expect(rules.find((r) => r.id === 'lower')?.met).toBe(true);
    expect(rules.find((r) => r.id === 'number')?.met).toBe(false);
    expect(rules.find((r) => r.id === 'special')?.met).toBe(false);
  });

  it('determines compliance with policy', () => {
    expect(isPasswordPolicyCompliant('Password123!')).toBe(true);
    expect(isPasswordPolicyCompliant('password123')).toBe(false);
    expect(isPasswordPolicyCompliant('PASSWORD123!')).toBe(false);
  });

  it('calculates password strength accurately', () => {
    expect(calculatePasswordStrength('').score).toBe(0);
    expect(calculatePasswordStrength('abc').score).toBe(1);
    expect(calculatePasswordStrength('Password123!').score).toBeGreaterThanOrEqual(4);
    expect(calculatePasswordStrength('SuperSecretPassword123!@#').score).toBe(5);
  });

  it('generates secure compliant passwords', () => {
    for (let i = 0; i < 5; i++) {
      const generated = generateSecurePassword(14);
      expect(generated.length).toBe(14);
      expect(isPasswordPolicyCompliant(generated)).toBe(true);
    }
  });

  it('validates reactive form controls with passwordPolicyValidator', () => {
    const controlValid = new FormControl('SecurePass123!');
    expect(passwordPolicyValidator(controlValid)).toBeNull();

    const controlInvalid = new FormControl('weak');
    expect(passwordPolicyValidator(controlInvalid)).toEqual({ passwordPolicy: true });

    const controlEmpty = new FormControl('');
    expect(passwordPolicyValidator(controlEmpty)).toBeNull();
  });
});
