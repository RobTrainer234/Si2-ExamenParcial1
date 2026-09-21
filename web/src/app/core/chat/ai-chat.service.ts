import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { appConfig } from '../config/app-config';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface SuggestedProduct {
  id: number;
  name: string;
  category_name: string;
  price: number;
  image_url: string | null;
  slug: string | null;
}

export interface SuggestedAction {
  label: string;
  action_type: string;
  payload: Record<string, any>;
}

export interface ChatResponse {
  reply: string;
  suggested_products: SuggestedProduct[];
  suggested_actions: SuggestedAction[];
  provider: string;
}

@Injectable({ providedIn: 'root' })
export class AiChatService {
  private readonly http = inject(HttpClient);

  sendMessage(message: string, history: ChatMessage[] = []): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${appConfig.apiBaseUrl}/ai/chat`, {
      message,
      history,
    });
  }
}
