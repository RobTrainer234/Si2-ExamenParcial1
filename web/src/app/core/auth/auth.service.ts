import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { appConfig } from '../config/app-config';
import { AuthResponse, UserSession } from '../models/api.models';

const SESSION_KEY = 'fashionstore_session';

interface StoredSession extends AuthResponse {}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly sessionState = signal<StoredSession | null>(this.readSession());
  readonly session = this.sessionState.asReadonly();

  constructor(private readonly http: HttpClient) {}

  register(data: { first_name: string; last_name: string; email: string; phone: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${appConfig.apiBaseUrl}/auth/register`, data).pipe(tap((response) => this.saveSession(response)));
  }

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${appConfig.apiBaseUrl}/auth/login`, { email, password }).pipe(tap((response) => this.saveSession(response)));
  }

  logout(): void {
    const refreshToken = this.sessionState()?.refresh_token;
    if (refreshToken) {
      this.http.post<void>(`${appConfig.apiBaseUrl}/auth/logout`, { refresh_token: refreshToken }).subscribe({ error: () => undefined });
    }
    localStorage.removeItem(SESSION_KEY);
    this.sessionState.set(null);
  }

  isAuthenticated(): boolean {
    return this.sessionState() !== null;
  }

  currentUser(): UserSession | null {
    return this.sessionState()?.user ?? null;
  }

  accessToken(): string | null {
    return this.sessionState()?.access_token ?? null;
  }

  private saveSession(response: AuthResponse): void {
    localStorage.setItem(SESSION_KEY, JSON.stringify(response));
    this.sessionState.set(response);
  }

  private readSession(): StoredSession | null {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      return stored ? (JSON.parse(stored) as StoredSession) : null;
    } catch {
      localStorage.removeItem(SESSION_KEY);
      return null;
    }
  }
}
