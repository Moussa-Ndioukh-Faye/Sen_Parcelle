// ═══════════════════════════════════════════════════════════════
// src/app/core/services/auth.service.ts
// Authentication avec Angular Signals
// ═══════════════════════════════════════════════════════════════

import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';
import { tap, catchError, map, switchMap } from 'rxjs/operators';
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
  private _pendingUserEmail = signal<string | null>(null);
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

  // La session est restaurée à la demande par les guards (ensureSession) :
  // l'appeler dans le constructeur passait par l'intercepteur JWT, qui dépend
  // lui-même de ce service, et la requête échouait en déconnectant l'utilisateur.

  // ──────────────────────────────────────────────
  // LOGIN
  // ──────────────────────────────────────────────

  login(payload: LoginPayload): Observable<LoginResponse> {
    this._isLoading.set(true);
    this._error.set(null);

    return this.api.post<LoginResponse>('/auth/login/', payload, false).pipe(
      switchMap(response => {
        if (response.requires_otp) {
          this._requiresOTP.set(true);
          this._pendingUserId.set(response.user_id ?? null);
          this._pendingUserEmail.set(payload.email);
          return of(response);
        }
        if (response.access_token) {
          this._saveTokens(response);
          // Charger le profil AVANT d'émettre : les guards le lisent dès la navigation
          return this.api.get<AuthUser>('/utilisateurs/moi/').pipe(
            tap(user => this._user.set(user)),
            map(() => response),
          );
        }
        return of(response);
      }),
      tap(() => this._isLoading.set(false)),
      catchError(err => {
        this._error.set(err.message ?? 'Connexion échouée');
        this._isLoading.set(false);
        return throwError(() => err);
      }),
    );
  }

  submitOTP(otpCode: string): Observable<LoginResponse> {
    const email = this._pendingUserEmail();
    return this.login({
      email: email ?? '',
      password: '',
      otp_code: otpCode,
    });
  }

  // ──────────────────────────────────────────────
  // LOGOUT
  // ──────────────────────────────────────────────

  logout(): void {
    this._clearTokens();
    this._user.set(null);
    this._requiresOTP.set(false);
    this._error.set(null);
    this.router.navigate(['/auth/login']);
  }

  private _clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_role');
  }

  // ──────────────────────────────────────────────
  // REFRESH TOKEN
  // ──────────────────────────────────────────────

  refreshToken(): Observable<{ access: string }> {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return throwError(() => new Error('No refresh token'));
    return this.api.post<{ access: string }>('/auth/token/refresh/', { refresh }, false).pipe(
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

  /**
   * Garantit que le profil est chargé si un token valide existe
   * (rechargement de page). Utilisé par les guards de navigation.
   */
  ensureSession(): Observable<boolean> {
    if (this._user()) return of(true);
    const token = this.getAccessToken();
    if (!token || this.isTokenExpired()) return of(false);
    return this.api.get<AuthUser>('/utilisateurs/moi/').pipe(
      tap(user => this._user.set(user)),
      map(() => true),
      catchError(() => of(false)),
    );
  }
}


// ═══════════════════════════════════════════════════════════════