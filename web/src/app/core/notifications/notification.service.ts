import { Injectable, signal } from '@angular/core';

export type NotificationKind = 'success' | 'error';

export interface NotificationMessage {
  id: number;
  kind: NotificationKind;
  message: string;
}

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private nextId = 1;
  private readonly messagesState = signal<NotificationMessage[]>([]);
  readonly messages = this.messagesState.asReadonly();

  success(message: string): void {
    this.show('success', message);
  }

  error(message: string): void {
    this.show('error', message);
  }

  dismiss(id: number): void {
    this.messagesState.update((messages) => messages.filter((item) => item.id !== id));
  }

  private show(kind: NotificationKind, message: string): void {
    const notification: NotificationMessage = { id: this.nextId++, kind, message };
    this.messagesState.update((messages) => [...messages, notification].slice(-4));
    window.setTimeout(() => this.dismiss(notification.id), 3800);
  }
}
