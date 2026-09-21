import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export interface PasswordRuleState {
  id: string;
  label: string;
  met: boolean;
}

export interface PasswordStrength {
  score: number; // 0 to 4
  label: 'Muy débil' | 'Débil' | 'Aceptable' | 'Segura' | 'Excelente';
  color: string;
  percent: number;
}

export function evaluatePasswordRules(password: string): PasswordRuleState[] {
  const pwd = password || '';
  return [
    {
      id: 'minLength',
      label: 'Mínimo 8 caracteres',
      met: pwd.length >= 8,
    },
    {
      id: 'upper',
      label: 'Al menos una letra mayúscula (A-Z)',
      met: /[A-Z]/.test(pwd),
    },
    {
      id: 'lower',
      label: 'Al menos una letra minúscula (a-z)',
      met: /[a-z]/.test(pwd),
    },
    {
      id: 'number',
      label: 'Al menos un número (0-9)',
      met: /[0-9]/.test(pwd),
    },
    {
      id: 'special',
      label: 'Al menos un carácter especial (!@#$...)',
      met: /[^A-Za-z0-9]/.test(pwd),
    },
  ];
}

export function isPasswordPolicyCompliant(password: string): boolean {
  const rules = evaluatePasswordRules(password);
  return rules.every((r) => r.met);
}

export function calculatePasswordStrength(password: string): PasswordStrength {
  if (!password) {
    return { score: 0, label: 'Muy débil', color: '#9ca3af', percent: 0 };
  }

  const rules = evaluatePasswordRules(password);
  const metCount = rules.filter((r) => r.met).length;
  const isLong = password.length >= 12;

  if (metCount <= 1) {
    return { score: 1, label: 'Muy débil', color: '#e11d48', percent: 20 };
  }
  if (metCount <= 3) {
    return { score: 2, label: 'Débil', color: '#f97316', percent: 45 };
  }
  if (metCount === 4) {
    return { score: 3, label: 'Aceptable', color: '#eab308', percent: 70 };
  }
  if (metCount === 5 && !isLong) {
    return { score: 4, label: 'Segura', color: '#8f6d2d', percent: 88 };
  }
  return { score: 5, label: 'Excelente', color: '#15803d', percent: 100 };
}

export function generateSecurePassword(length = 14): string {
  const uppers = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
  const lowers = 'abcdefghijkmnopqrstuvwxyz';
  const numbers = '23456789';
  const specials = '!@#$%^&*()_+~-=[]{}';
  const all = uppers + lowers + numbers + specials;

  // Pick at least one from each
  const randomPick = (chars: string) => chars[Math.floor(Math.random() * chars.length)];
  const pwdChars = [
    randomPick(uppers),
    randomPick(lowers),
    randomPick(numbers),
    randomPick(specials),
  ];

  for (let i = pwdChars.length; i < length; i++) {
    pwdChars.push(randomPick(all));
  }

  // Shuffle
  for (let i = pwdChars.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pwdChars[i], pwdChars[j]] = [pwdChars[j], pwdChars[i]];
  }

  return pwdChars.join('');
}

export const passwordPolicyValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value = control.value;
  if (!value) return null; // let Validators.required handle empty
  if (!isPasswordPolicyCompliant(value)) {
    return { passwordPolicy: true };
  }
  return null;
};
