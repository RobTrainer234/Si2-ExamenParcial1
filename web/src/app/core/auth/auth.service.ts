import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { appConfig } from '../config/app-config';
import { AuthResponse, UserSession } from '../models/api.models';
import { OfflineCatalogService } from '../offline/offline-catalog.service';
import { OfflineTransactionService } from '../offline/offline-transaction.service';

const SESSION_KEY = 'fashionstore_session';

interface StoredSession extends AuthResponse {}

export interface EmailVerificationStartResponse {
  accepted: boolean;
  email_sent: boolean;
}

export interface EmailVerificationResponse {
  verified: boolean;
  checkout_capability: string;
}

export interface PaidCheckoutResponse {
  session_id: string;
  session_url: string;
}

export interface PaidCheckoutStatusResponse {
  status: 'PENDING' | 'CHECKOUT_CREATED' | 'COMPLETED' | 'EXPIRED' | 'EMAIL_CONFLICT' | 'ERROR';
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly sessionState = signal<StoredSession | null>(this.readSession());
  readonly session = this.sessionState.asReadonly();

  constructor(
    private readonly http: HttpClient,
    private readonly offlineCatalog: OfflineCatalogService,
    private readonly offlineTx: OfflineTransactionService,
  ) {}

  register(data: { first_name: string; last_name: string; email: string; phone: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${appConfig.apiBaseUrl}/auth/register`, data).pipe(tap((response) => this.saveSession(response)));
  }

  registerCompanyTrial(data: {
    company_name: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    password: string;
  }): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${appConfig.apiBaseUrl}/subscriptions/trial-signup`, data)
      .pipe(tap((response) => this.saveSession(response)));
  }

  startEmailVerification(email: string): Observable<EmailVerificationStartResponse> {
    return this.http.post<EmailVerificationStartResponse>(`${appConfig.apiBaseUrl}/subscriptions/email-verification/start`, { email });
  }

  verifyEmail(email: string, code: string): Observable<EmailVerificationResponse> {
    return this.http.post<EmailVerificationResponse>(`${appConfig.apiBaseUrl}/subscriptions/email-verification/verify`, { email, code });
  }

  registerPaidCheckout(data: {
    company_name: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
    password: string;
    plan_code: string;
    billing_interval: 'monthly' | 'annual';
    checkout_capability: string;
  }): Observable<PaidCheckoutResponse> {
    return this.http.post<PaidCheckoutResponse>(`${appConfig.apiBaseUrl}/subscriptions/paid-checkout`, data);
  }

  getPaidCheckoutStatus(sessionId: string): Observable<PaidCheckoutStatusResponse> {
    return this.http.get<PaidCheckoutStatusResponse>(`${appConfig.apiBaseUrl}/subscriptions/paid-checkout/status`, {
      params: { session_id: sessionId },
    });
  }

  defaultHomeRoute(): string {
    const user = this.currentUser();
    if (!user) return '/catalog';
    switch (user.role) {
      case 'PLATFORM_ADMIN':
        return '/platform';
      case 'ADMIN':
        return '/admin';
      case 'BRANCH_MANAGER':
      case 'OPERATOR':
        return '/operations';
      case 'CASHIER':
      case 'SELLER':
        return '/pos';
      case 'SUPPLIER':
        return '/supplier';
      default:
        return '/catalog';
    }
  }

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${appConfig.apiBaseUrl}/auth/login`, { email, password }).pipe(tap((response) => this.saveSession(response)));
  }

  logout(): void {
    const refreshToken = this.sessionState()?.refresh_token;
    if (refreshToken) {
      this.http.post<void>(`${appConfig.apiBaseUrl}/auth/logout`, { refresh_token: refreshToken }).subscribe({ error: () => undefined });
    }
    this.clearSession();
  }

  clearSession(): void {
    localStorage.removeItem(SESSION_KEY);
    this.sessionState.set(null);
    void this.offlineCatalog.clearCache();
    void this.offlineTx.clearAllOperations();
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

  hasPermission(permission: string): boolean {
    const user = this.currentUser();
    return user?.role === 'ADMIN' || Boolean(user?.permissions?.includes(permission));
  }

  private saveSession(response: AuthResponse): void {
    const prev = this.sessionState();
    if (prev && (prev.user.tenant_id !== response.user.tenant_id || prev.user.id !== response.user.id)) {
      void this.offlineCatalog.clearCache();
      void this.offlineTx.clearAllOperations();
    }
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
