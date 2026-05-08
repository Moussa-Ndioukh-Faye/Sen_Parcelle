// ═══════════════════════════════════════════════════════════════
// src/app/core/services/auth.service.ts
// Authentication avec Angular Signals
// ═══════════════════════════════════════════════════════════════

import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';

export interface AuthUser {
  id:         string;
  nom:        string;
  email:      string;
  role:       string;
  kyc_status: string;
}

export interface LoginPayload {
  email:     string;
  password:  string;
  otp_code?: string;
}

export interface LoginResponse {
  access_token?:  string;
  refresh_token?: string;
  user_id?:       string;
  role?:          string;
  requires_otp?:  boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {

  private readonly api    = inject(ApiService);
  private readonly router = inject(Router);

  // ─── Signals d'état ───
  private _user         = signal<AuthUser | null>(null);
  private _requiresOTP  = signal(false);
  private _pendingUserId = signal<string | null>(null);
  private _isLoading    = signal(false);
  private _error        = signal<string | null>(null);

  // ─── Computed publics (readonly) ───
  readonly user           = this._user.asReadonly();
  readonly requiresOTP    = this._requiresOTP.asReadonly();
  readonly isLoading      = this._isLoading.asReadonly();
  readonly error          = this._error.asReadonly();
  readonly isAuthenticated = computed(() => this._user() !== null);
  readonly isAdmin        = computed(() => this._user()?.role === 'admin');
  readonly userInitials   = computed(() => {
    const nom = this._user()?.nom ?? '';
    return nom.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  });

  constructor() {
    // Restaurer la session au démarrage
    this._restoreSession();
  }

  // ──────────────────────────────────────────────
  // LOGIN
  // ──────────────────────────────────────────────

  login(payload: LoginPayload): Observable<LoginResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<LoginResponse>('/auth/login/', payload, false).pipe(
      tap(response => {
        if (response.requires_otp) {
          this._requiresOTP.set(true);
          this._pendingUserId.set(response.user_id ?? null);
        } else if (response.access_token) {
          this._saveTokens(response);
          this._loadCurrentUser();
        }
        this._isLoading.set(false);
      }),
      catchError(err => {
        this._error.set(err.message ?? 'Connexion échouée');
        this._isLoading.set(false);
        return throwError(() => err);
      }),
    );
  }

  submitOTP(otpCode: string): Observable<LoginResponse> {
    return this.login({
      email:    '',     // Le backend identifie par userId en session
      password: '',
      otp_code: otpCode,
    });
  }

  // ──────────────────────────────────────────────
  // LOGOUT
  // ──────────────────────────────────────────────

  logout(): void {
    localStorage.clear();
    this._user.set(null);
    this._requiresOTP.set(false);
    this._error.set(null);
    this.router.navigate(['/auth/login']);
  }

  // ──────────────────────────────────────────────
  // REFRESH TOKEN
  // ──────────────────────────────────────────────

  refreshToken(): Observable<{ access: string }> {
    const refresh = localStorage.getItem('refresh_token');
    return this.api.post<{ access: string }>('/auth/refresh/', { refresh }, false).pipe(
      tap(response => {
        localStorage.setItem('access_token', response.access);
      }),
    );
  }

  // ──────────────────────────────────────────────
  // TOKEN HELPERS
  // ──────────────────────────────────────────────

  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isTokenExpired(): boolean {
    const token = this.getAccessToken();
    if (!token) return true;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  }

  getRoleFromToken(): string | null {
    const token = this.getAccessToken();
    if (!token) return null;
    try {
      return JSON.parse(atob(token.split('.')[1])).role ?? null;
    } catch {
      return null;
    }
  }

  // ──────────────────────────────────────────────
  // PRIVATE
  // ──────────────────────────────────────────────

  private _saveTokens(response: LoginResponse): void {
    if (response.access_token)  localStorage.setItem('access_token',  response.access_token);
    if (response.refresh_token) localStorage.setItem('refresh_token', response.refresh_token);
    if (response.user_id)       localStorage.setItem('user_id',       response.user_id);
    if (response.role)          localStorage.setItem('user_role',     response.role);
  }

  private _loadCurrentUser(): void {
    this.api.get<AuthUser>('/utilisateurs/moi/').subscribe({
      next:  user => this._user.set(user),
      error: ()   => this.logout(),
    });
  }

  private _restoreSession(): void {
    const token = this.getAccessToken();
    if (token && !this.isTokenExpired()) {
      this._loadCurrentUser();
    }
  }
}


// ═══════════════════════════════════════════════════════════════