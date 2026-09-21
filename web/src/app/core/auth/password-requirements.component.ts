import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import {
  PasswordRuleState,
  PasswordStrength,
  calculatePasswordStrength,
  evaluatePasswordRules,
} from './password-security.helper';

@Component({
  selector: 'app-password-requirements',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="password-requirements-card" [class.compact]="compact">
      @if (showStrength && password) {
        <div class="strength-meter-block">
          <div class="strength-header">
            <span class="strength-title">Seguridad:</span>
            <span class="strength-tag" [style.color]="strength.color">
              <strong>{{ strength.label }}</strong>
            </span>
          </div>
          <div class="strength-bar-track">
            <div
              class="strength-bar-fill"
              [style.width.%]="strength.percent"
              [style.background-color]="strength.color"
            ></div>
          </div>
        </div>
      }

      <div class="rules-header">
        <span class="rules-title">Requisitos de la contraseña:</span>
      </div>

      <ul class="rules-list" role="list">
        @for (rule of rules; track rule.id) {
          <li class="rule-item" [class.met]="rule.met">
            <span class="rule-icon" aria-hidden="true">
              @if (rule.met) {
                <svg class="check-svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              } @else {
                <span class="circle-bullet"></span>
              }
            </span>
            <span class="rule-label">{{ rule.label }}</span>
          </li>
        }
      </ul>
    </div>
  `,
  styles: [`
    .password-requirements-card {
      background: #fbf9f5;
      border: 1px solid #e7e2d9;
      border-radius: 8px;
      padding: 12px 14px;
      margin-top: 6px;
      text-align: left;
      transition: all 0.2s ease;
    }
    .password-requirements-card.compact {
      padding: 10px 12px;
      font-size: 0.85em;
    }
    .strength-meter-block {
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px dashed #e2dcce;
    }
    .strength-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.72rem;
      margin-bottom: 5px;
    }
    .strength-title {
      color: #6b6357;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 0.65rem;
      font-weight: 600;
    }
    .strength-tag strong {
      font-size: 0.72rem;
      letter-spacing: 0.04em;
    }
    .strength-bar-track {
      height: 4px;
      background: #e9e4da;
      border-radius: 999px;
      overflow: hidden;
    }
    .strength-bar-fill {
      height: 100%;
      border-radius: 999px;
      transition: width 0.3s ease, background-color 0.3s ease;
    }
    .rules-header {
      margin-bottom: 6px;
    }
    .rules-title {
      font-size: 0.67rem;
      color: #786f61;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .rules-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .rule-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.75rem;
      color: #797164;
      transition: color 0.2s ease;
    }
    .rule-item.met {
      color: #1b1c1a;
      font-weight: 500;
    }
    .rule-icon {
      width: 16px;
      height: 16px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .check-svg {
      width: 15px;
      height: 15px;
      color: #15803d;
      animation: popIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .circle-bullet {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #cfc7b9;
      display: inline-block;
      transition: background 0.2s ease;
    }
    .rule-item.met .circle-bullet {
      background: #15803d;
    }
    @keyframes popIn {
      0% { transform: scale(0.6); opacity: 0; }
      100% { transform: scale(1); opacity: 1; }
    }
  `],
})
export class PasswordRequirementsComponent {
  @Input() password = '';
  @Input() showStrength = true;
  @Input() compact = false;

  get rules(): PasswordRuleState[] {
    return evaluatePasswordRules(this.password);
  }

  get strength(): PasswordStrength {
    return calculatePasswordStrength(this.password);
  }
}
