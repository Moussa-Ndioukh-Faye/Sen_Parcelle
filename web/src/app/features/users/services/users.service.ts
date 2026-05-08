// src/app/features/users/services/users.service.ts
// ═══════════════════════════════════════════════════════════════

import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { ApiService } from '@core/services/api.service';
import {
  User, UserDetail, PaginatedResponse, KYCStatus, AuditLog
} from '@core/models';

export interface UserFilters {
  role?:       string;
  kyc_status?: string;
  search?:     string;
  page?:       number;
}

@Injectable({ providedIn: 'root' })
export class UsersService {

  private readonly api  = inject(ApiService);

  private _users        = signal<User[]>([]);
  private _total        = signal(0);
  private _isLoading    = signal(false);

  readonly users        = this._users.asReadonly();
  readonly total        = this._total.asReadonly();
  readonly isLoading    = this._isLoading.asReadonly();

  // ──────────────────────────────────────────────
  // LECTURE
  // ──────────────────────────────────────────────

  fetchUsers(filters: UserFilters = {}): Observable<PaginatedResponse<User>> {
    this._isLoading.set(true);

    const params: Record<string, string | number> = {
      page: filters.page ?? 1,
    };
    if (filters.role)       params['role']       = filters.role;
    if (filters.kyc_status) params['kyc_status'] = filters.kyc_status;
    if (filters.search)     params['search']     = filters.search;

    return this.api.get<PaginatedResponse<User>>('/utilisateurs/', params).pipe(
      tap(response => {
        this._users.set(response.results);
        this._total.set(response.count);
        this._isLoading.set(false);
      }),
    );
  }

  fetchUserById(id: string): Observable<UserDetail> {
    return this.api.get<UserDetail>(`/utilisateurs/${id}/`);
  }

  fetchPendingKYC(): Observable<PaginatedResponse<User>> {
    return this.fetchUsers({ kyc_status: 'pending', page: 1 });
  }

  // ──────────────────────────────────────────────
  // KYC ACTIONS
  // ──────────────────────────────────────────────

  approveKYC(userId: string): Observable<{ kyc_status: string; message: string }> {
    return this.api.post(`/utilisateurs/${userId}/kyc/`, {
      decision: 'approve',
    }).pipe(
      tap(() => this._updateUserKYC(userId, 'verified')),
    );
  }

  rejectKYC(userId: string, reason: string): Observable<{ kyc_status: string; message: string }> {
    return this.api.post(`/utilisateurs/${userId}/kyc/`, {
      decision: 'reject',
      reason,
    }).pipe(
      tap(() => this._updateUserKYC(userId, 'rejected')),
    );
  }

  // ──────────────────────────────────────────────
  // GESTION COMPTE
  // ──────────────────────────────────────────────

  suspendUser(userId: string): Observable<{ message: string }> {
    return this.api.patch(`/utilisateurs/${userId}/`, { is_active: false }).pipe(
      tap(() => this._updateUserActive(userId, false)),
    );
  }

  activateUser(userId: string): Observable<{ message: string }> {
    return this.api.patch(`/utilisateurs/${userId}/`, { is_active: true }).pipe(
      tap(() => this._updateUserActive(userId, true)),
    );
  }

  // ──────────────────────────────────────────────
  // AUDIT
  // ──────────────────────────────────────────────

  getUserAuditLogs(userId: string): Observable<AuditLog[]> {
    return this.api.get<AuditLog[]>(`/audit/user/${userId}/`);
  }

  getSecurityEvents(): Observable<AuditLog[]> {
    return this.api.get<AuditLog[]>('/audit/security/');
  }

  // ──────────────────────────────────────────────
  // PRIVATE HELPERS
  // ──────────────────────────────────────────────

  private _updateUserKYC(userId: string, status: KYCStatus): void {
    this._users.update(users =>
      users.map(u => u.id === userId ? { ...u, kyc_status: status } : u)
    );
  }

  private _updateUserActive(userId: string, isActive: boolean): void {
    this._users.update(users =>
      users.map(u => u.id === userId ? { ...u, is_active: isActive } : u)
    );
  }
}


// ═══════════════════════════════════════════════════════════════