import { Component, inject } from '@angular/core';
import { CommonModule, CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AiChatService, ChatMessage, SuggestedAction, SuggestedProduct } from '../../core/chat/ai-chat.service';

interface DisplayMessage {
  role: 'user' | 'assistant';
  content: string;
  products?: SuggestedProduct[];
  actions?: SuggestedAction[];
  time: string;
}

@Component({
  selector: 'app-ai-chat-widget',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, CurrencyPipe],
  template: `
    <!-- Floating Trigger Button -->
    <div class="ai-widget-container">
      @if (!isOpen) {
        <button
          type="button"
          class="ai-trigger-button"
          (click)="toggleOpen()"
          aria-label="Abrir Asistente Virtual Inteligente"
        >
          <span class="ai-trigger-sparkle">
            <span class="material-symbols-outlined">auto_awesome</span>
          </span>
          <div class="ai-trigger-text">
            <span class="ai-trigger-label">Sofía · Personal Shopper IA</span>
            <small class="ai-trigger-sub">Motor Inteligente Activo</small>
          </div>
          <span class="ai-online-dot"></span>
        </button>
      }

      <!-- Floating Chat Dialog Window -->
      @if (isOpen) {
        <div class="ai-chat-card" role="dialog" aria-labelledby="chat-title">
          <!-- Luxury Header -->
          <header class="ai-chat-header">
            <div class="ai-header-info">
              <div class="ai-avatar">
                <span class="material-symbols-outlined">auto_awesome</span>
              </div>
              <div class="ai-header-text">
                <h3 id="chat-title">Sofía · Personal Shopper IA</h3>
                <small class="ai-status-row">
                  <span class="status-indicator"></span>
                  <span>Motor Inteligente Local · En línea</span>
                </small>
              </div>
            </div>
            <button
              type="button"
              class="ai-close-btn"
              (click)="toggleOpen()"
              aria-label="Cerrar chat"
            >
              <span class="material-symbols-outlined">close</span>
            </button>
          </header>

          <!-- Thread of Messages -->
          <div class="ai-messages-list" #messagesContainer>
            @for (msg of messages; track $index) {
              <div class="ai-message-row" [class.user-row]="msg.role === 'user'">
                @if (msg.role === 'assistant') {
                  <div class="ai-msg-avatar">
                    <span class="material-symbols-outlined">psychology</span>
                  </div>
                }
                <div class="ai-bubble" [class.user-bubble]="msg.role === 'user'">
                  <p class="ai-text">{{ msg.content }}</p>

                  <!-- Suggested Products Cards inside message -->
                  @if (msg.products && msg.products.length > 0) {
                    <div class="ai-products-grid">
                      @for (prod of msg.products; track prod.id) {
                        <div class="ai-product-card">
                          @if (prod.image_url) {
                            <img [src]="prod.image_url" [alt]="prod.name" class="ai-product-img" />
                          } @else {
                            <div class="ai-product-placeholder">
                              <span class="material-symbols-outlined">apparel</span>
                            </div>
                          }
                          <div class="ai-product-details">
                            <span class="ai-product-cat">{{ prod.category_name }}</span>
                            <strong class="ai-product-name">{{ prod.name }}</strong>
                            <span class="ai-product-price">{{ prod.price | currency:'BOB':'symbol':'1.2-2' }}</span>
                          </div>
                          <a
                            [routerLink]="['/catalog', prod.id]"
                            (click)="toggleOpen()"
                            class="ai-view-btn"
                          >
                            <span>Ver prenda</span>
                            <span class="material-symbols-outlined">chevron_right</span>
                          </a>
                        </div>
                      }
                    </div>
                  }

                  <!-- Suggested Action Chips inside message -->
                  @if (msg.actions && msg.actions.length > 0) {
                    <div class="ai-actions-row">
                      @for (action of msg.actions; track action.label) {
                        <button
                          type="button"
                          class="ai-action-chip"
                          (click)="handleAction(action)"
                        >
                          <span class="material-symbols-outlined">arrow_outward</span>
                          <span>{{ action.label }}</span>
                        </button>
                      }
                    </div>
                  }
                  <span class="ai-timestamp">{{ msg.time }}</span>
                </div>
              </div>
            }

            @if (isLoading) {
              <div class="ai-message-row">
                <div class="ai-msg-avatar">
                  <span class="material-symbols-outlined">psychology</span>
                </div>
                <div class="ai-bubble ai-typing-indicator">
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                </div>
              </div>
            }
          </div>

          <!-- Quick Suggestions Chips Bar -->
          <div class="ai-quick-prompts">
            <button type="button" class="quick-chip" (click)="sendQuickPrompt('¿Qué promociones o descuentos tienen hoy?')">
              <span>🏷️ Promociones</span>
            </button>
            <button type="button" class="quick-chip" (click)="sendQuickPrompt('¿Cómo uso el vestidor virtual con realidad aumentada?')">
              <span>👗 Vestidor AR</span>
            </button>
            <button type="button" class="quick-chip" (click)="sendQuickPrompt('¿Cómo hago una reserva para probarme en sucursal?')">
              <span>🏬 Reservar en tienda</span>
            </button>
            <button type="button" class="quick-chip" (click)="sendQuickPrompt('Recomiéndame ropa elegante de temporada')">
              <span>✨ Recomendaciones</span>
            </button>
          </div>

          <!-- Input Bar with Voice & Send -->
          <form class="ai-input-bar" (ngSubmit)="sendMessage()">
            <div class="ai-input-wrapper">
              <input
                type="text"
                name="chatInput"
                [(ngModel)]="inputText"
                [disabled]="isLoading"
                placeholder="Escribe tu consulta sobre prendas, sucursales o vestidor..."
                autocomplete="off"
              />
              @if (isVoiceSupported) {
                <button
                  type="button"
                  class="ai-voice-btn"
                  [class.listening]="isListening"
                  (click)="toggleVoiceInput()"
                  [title]="isListening ? 'Detener dictado' : 'Dictar por voz'"
                >
                  <span class="material-symbols-outlined">{{ isListening ? 'mic' : 'mic_none' }}</span>
                </button>
              }
            </div>
            <button
              type="submit"
              class="ai-send-btn"
              [disabled]="isLoading || !inputText.trim()"
              aria-label="Enviar mensaje"
            >
              <span class="material-symbols-outlined">send</span>
            </button>
          </form>
        </div>
      }
    </div>
  `,
  styles: [`
    .ai-widget-container {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 9999;
      font-family: inherit;
    }

    /* Floating Trigger Button */
    .ai-trigger-button {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      background: linear-gradient(135deg, #181614 0%, #29241e 100%);
      color: #ffffff;
      border: 1px solid rgba(212, 175, 55, 0.45);
      padding: 0.75rem 1.4rem;
      border-radius: 9999px;
      cursor: pointer;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28), 0 0 16px rgba(212, 175, 55, 0.2);
      transition: all 0.25s ease;
    }

    .ai-trigger-button:hover {
      transform: translateY(-3px);
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.35), 0 0 22px rgba(212, 175, 55, 0.35);
      border-color: #d4af37;
    }

    .ai-trigger-sparkle {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: linear-gradient(135deg, #b8924a 0%, #d4af37 100%);
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(212, 175, 55, 0.4);
    }

    .ai-trigger-sparkle .material-symbols-outlined {
      font-size: 18px;
    }

    .ai-trigger-text {
      display: flex;
      flex-direction: column;
      text-align: left;
    }

    .ai-trigger-label {
      font-size: 0.88rem;
      font-weight: 600;
      color: #ffffff;
      line-height: 1.2;
    }

    .ai-trigger-sub {
      font-size: 0.68rem;
      color: #d4af37;
      letter-spacing: 0.02em;
    }

    .ai-online-dot {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10b981;
      animation: pulse-ring 2s infinite;
    }

    @keyframes pulse-ring {
      0% { transform: scale(0.9); opacity: 0.8; }
      50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 12px #10b981; }
      100% { transform: scale(0.9); opacity: 0.8; }
    }

    /* Floating Chat Dialog Window */
    .ai-chat-card {
      width: 410px;
      max-width: calc(100vw - 2rem);
      height: 570px;
      max-height: calc(100vh - 3.5rem);
      background: #ffffff;
      border-radius: 20px;
      border: 1px solid rgba(212, 175, 55, 0.35);
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.25);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      animation: chat-popup 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes chat-popup {
      from { opacity: 0; transform: translateY(16px) scale(0.96); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* Luxury Header */
    .ai-chat-header {
      background: linear-gradient(135deg, #161412 0%, #24201a 100%);
      color: #ffffff;
      padding: 1rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(212, 175, 55, 0.25);
    }

    .ai-header-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .ai-avatar {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, #8f6d2d 0%, #d4af37 100%);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(212, 175, 55, 0.35);
    }

    .ai-avatar .material-symbols-outlined {
      font-size: 20px;
    }

    .ai-header-text h3 {
      margin: 0;
      font-family: 'Playfair Display', Georgia, serif;
      font-size: 1.05rem;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: #ffffff;
    }

    .ai-status-row {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.7rem;
      color: #d4af37;
    }

    .status-indicator {
      width: 6px;
      height: 6px;
      background: #10b981;
      border-radius: 50%;
      display: inline-block;
      box-shadow: 0 0 6px #10b981;
    }

    .ai-close-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 50%;
      width: 32px;
      height: 32px;
      color: #b8b0a2;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .ai-close-btn:hover {
      background: rgba(255, 255, 255, 0.18);
      color: #ffffff;
    }

    .ai-close-btn .material-symbols-outlined {
      font-size: 18px;
    }

    /* Thread of Messages */
    .ai-messages-list {
      flex: 1;
      overflow-y: auto;
      padding: 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      background: #faf8f5;
    }

    .ai-message-row {
      display: flex;
      gap: 0.6rem;
      align-items: flex-start;
    }

    .ai-message-row.user-row {
      justify-content: flex-end;
    }

    .ai-msg-avatar {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #f0eae1;
      border: 1px solid rgba(212, 175, 55, 0.3);
      color: #8f6d2d;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 2px;
    }

    .ai-msg-avatar .material-symbols-outlined {
      font-size: 16px;
    }

    .ai-bubble {
      max-width: 84%;
      background: #ffffff;
      border: 1px solid #e8e2d8;
      border-left: 3px solid #d4af37;
      border-radius: 14px;
      border-top-left-radius: 4px;
      padding: 0.8rem 1rem;
      font-size: 0.86rem;
      line-height: 1.45;
      color: #1f2937;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }

    .ai-bubble.user-bubble {
      background: #1a1815;
      color: #ffffff;
      border: 1px solid #1a1815;
      border-left: 1px solid #1a1815;
      border-radius: 14px;
      border-top-right-radius: 4px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .ai-text {
      margin: 0;
      white-space: pre-wrap;
    }

    .ai-timestamp {
      display: block;
      font-size: 0.65rem;
      color: #a8a29e;
      margin-top: 0.4rem;
      text-align: right;
    }

    .user-bubble .ai-timestamp {
      color: #8f8b82;
    }

    /* Products suggested inside bubble */
    .ai-products-grid {
      margin-top: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .ai-product-card {
      display: flex;
      gap: 0.65rem;
      background: #faf8f5;
      border: 1px solid #e8e2d8;
      border-radius: 10px;
      padding: 0.5rem;
      align-items: center;
      transition: all 0.2s ease;
    }

    .ai-product-card:hover {
      border-color: #d4af37;
      background: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    .ai-product-img, .ai-product-placeholder {
      width: 50px;
      height: 50px;
      border-radius: 8px;
      object-fit: cover;
      background: #ede8df;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #8f6d2d;
      flex-shrink: 0;
    }

    .ai-product-details {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 1px;
    }

    .ai-product-cat {
      font-size: 0.65rem;
      font-weight: 600;
      color: #8f6d2d;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .ai-product-name {
      font-size: 0.8rem;
      color: #1a1815;
      font-weight: 600;
      line-height: 1.2;
    }

    .ai-product-price {
      font-size: 0.82rem;
      font-weight: 700;
      color: #10b981;
    }

    .ai-view-btn {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      font-size: 0.72rem;
      font-weight: 600;
      color: #1a1815;
      background: #ede8df;
      padding: 0.35rem 0.6rem;
      border-radius: 999px;
      text-decoration: none;
      transition: all 0.2s ease;
    }

    .ai-view-btn:hover {
      background: #1a1815;
      color: #d4af37;
    }

    .ai-view-btn .material-symbols-outlined {
      font-size: 14px;
    }

    /* Actions row */
    .ai-actions-row {
      margin-top: 0.65rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }

    .ai-action-chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #fdfaf3;
      color: #8f6d2d;
      border: 1px solid #ebd9b0;
      border-radius: 999px;
      padding: 0.3rem 0.75rem;
      font-size: 0.74rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .ai-action-chip:hover {
      background: #8f6d2d;
      color: #ffffff;
      border-color: #8f6d2d;
    }

    .ai-action-chip .material-symbols-outlined {
      font-size: 13px;
    }

    /* Typing indicator */
    .ai-typing-indicator {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 0.8rem 1.1rem;
    }

    .typing-dot {
      width: 7px;
      height: 7px;
      background: #d4af37;
      border-radius: 50%;
      animation: typing-wave 1.3s infinite ease-in-out both;
    }

    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes typing-wave {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
      40% { transform: scale(1.1); opacity: 1; }
    }

    /* Quick suggestions bar */
    .ai-quick-prompts {
      display: flex;
      gap: 0.4rem;
      overflow-x: auto;
      padding: 0.6rem 0.85rem;
      background: #ffffff;
      border-top: 1px solid #f0eae1;
      scrollbar-width: none;
    }

    .quick-chip {
      white-space: nowrap;
      background: #faf8f5;
      border: 1px solid #e8e2d8;
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      font-size: 0.74rem;
      color: #4a453d;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .quick-chip:hover {
      background: #1a1815;
      color: #d4af37;
      border-color: #1a1815;
    }

    /* Input Bar */
    .ai-input-bar {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: #ffffff;
      border-top: 1px solid #e8e2d8;
    }

    .ai-input-wrapper {
      flex: 1;
      display: flex;
      align-items: center;
      background: #f7f5f0;
      border: 1px solid #e5dfd5;
      border-radius: 999px;
      padding: 0.25rem 0.5rem 0.25rem 0.85rem;
      transition: all 0.2s ease;
    }

    .ai-input-wrapper:focus-within {
      border-color: #d4af37;
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.15);
    }

    .ai-input-wrapper input {
      flex: 1;
      border: none;
      background: transparent;
      padding: 0.35rem 0;
      font-size: 0.84rem;
      outline: none;
      color: #1a1815;
    }

    .ai-voice-btn {
      background: transparent;
      border: none;
      color: #787166;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 4px;
      border-radius: 50%;
      transition: all 0.2s ease;
    }

    .ai-voice-btn:hover {
      color: #d4af37;
    }

    .ai-voice-btn.listening {
      color: #ef4444;
      background: rgba(239, 68, 68, 0.12);
      animation: pulse 1.2s infinite;
    }

    .ai-send-btn {
      background: #1a1815;
      border: 1px solid #1a1815;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #d4af37;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }

    .ai-send-btn:hover:not(:disabled) {
      background: #8f6d2d;
      border-color: #8f6d2d;
      color: #ffffff;
      transform: scale(1.05);
    }

    .ai-send-btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .ai-send-btn .material-symbols-outlined {
      font-size: 18px;
    }
  `],
})
export class AiChatWidgetComponent {
  private readonly chatService = inject(AiChatService);
  private readonly router = inject(Router);

  isOpen = false;
  isLoading = false;
  inputText = '';
  isListening = false;
  isVoiceSupported = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);
  private speechRecognition: any = null;

  messages: DisplayMessage[] = [
    {
      role: 'assistant',
      content: '¡Hola! Soy Sofía, tu asesora de moda y personal shopper en FashionStore 👗✨. ¿En qué te puedo asesorar hoy?',
      time: this.currentTime(),
    },
  ];

  toggleOpen(): void {
    this.isOpen = !this.isOpen;
  }

  currentTime(): string {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  sendQuickPrompt(prompt: string): void {
    this.inputText = prompt;
    this.sendMessage();
  }

  sendMessage(): void {
    const text = this.inputText.trim();
    if (!text || this.isLoading) return;

    this.messages.push({
      role: 'user',
      content: text,
      time: this.currentTime(),
    });
    this.inputText = '';
    this.isLoading = true;

    const historyPayload: ChatMessage[] = this.messages.slice(-6).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    this.chatService.sendMessage(text, historyPayload).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.messages.push({
          role: 'assistant',
          content: res.reply,
          products: res.suggested_products,
          actions: res.suggested_actions,
          time: this.currentTime(),
        });
      },
      error: () => {
        this.isLoading = false;
        this.messages.push({
          role: 'assistant',
          content: 'Disculpa, tuve un problema temporal al procesar tu solicitud. Intenta nuevamente en unos segundos.',
          time: this.currentTime(),
        });
      },
    });
  }

  handleAction(action: SuggestedAction): void {
    if (action.action_type === 'navigate' && action.payload?.['url']) {
      this.toggleOpen();
      this.router.navigateByUrl(action.payload['url']);
    }
  }

  toggleVoiceInput(): void {
    if (!this.isVoiceSupported) return;
    if (this.isListening) {
      this.speechRecognition?.stop();
      this.isListening = false;
      return;
    }

    try {
      const SpeechClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      this.speechRecognition = new SpeechClass();
      this.speechRecognition.lang = 'es-BO';
      this.speechRecognition.continuous = false;
      this.speechRecognition.interimResults = false;
      this.isListening = true;

      this.speechRecognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          this.inputText = transcript;
          this.isListening = false;
          this.sendMessage();
        }
      };

      this.speechRecognition.onerror = () => {
        this.isListening = false;
      };

      this.speechRecognition.onend = () => {
        this.isListening = false;
      };

      this.speechRecognition.start();
    } catch {
      this.isListening = false;
    }
  }
}
