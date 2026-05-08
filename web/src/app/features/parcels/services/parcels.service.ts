// ═══════════════════════════════════════════════════════════════
// src/app/features/parcels/services/parcels.service.ts
// ═══════════════════════════════════════════════════════════════

import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { ApiService } from '@core/services/api.service';
import {
  Parcel, ParcelDetail, PaginatedResponse, ValidationDecision
} from '@core/models';

export interface ParcelFilters {
  status?:      string;
  region?:      string;
  type_terrain?: string;
  search?:      string;
  page?:        number;
  page_size?:   number;
}

@Injectable({ providedIn: 'root' })
export class ParcelsService {

  private readonly api = inject(ApiService);

  // ─── Signals d'état ───
  private _parcels      = signal<Parcel[]>([]);
  private _total        = signal(0);
  private _isLoading    = signal(false);
  private _selectedId   = signal<string | null>(null);

  // ─── Computed ───
  readonly parcels      = this._parcels.asReadonly();
  readonly total        = this._total.asReadonly();
  readonly isLoading    = this._isLoading.asReadonly();
  readonly pendingCount = computed(() =>
    this._parcels().filter(p => p.status === 'pending').length
  );

  // ──────────────────────────────────────────────
  // LECTURE
  // ──────────────────────────────────────────────

  fetchParcels(filters: ParcelFilters = {}): Observable<PaginatedResponse<Parcel>> {
    this._isLoading.set(true);

    const params: Record<string, string | number | boolean> = {
      page: filters.page ?? 1,
    };
    if (filters.status)       params['status']       = filters.status;
    if (filters.region)       params['region']       = filters.region;
    if (filters.type_terrain) params['type_terrain'] = filters.type_terrain;
    if (filters.search)       params['search']       = filters.search;

    return this.api.get<PaginatedResponse<Parcel>>('/parcelles/', params).pipe(
      tap(response => {
        this._parcels.set(response.results);
        this._total.set(response.count);
        this._isLoading.set(false);
      }),
    );
  }

  fetchPending(): Observable<PaginatedResponse<Parcel>> {
    return this.fetchParcels({ status: 'pending', page_size: 50 });
  }

  fetchParcelById(id: string): Observable<ParcelDetail> {
    return this.api.get<ParcelDetail>(`/parcelles/${id}/`);
  }

  // ──────────────────────────────────────────────
  // ACTIONS ADMIN
  // ──────────────────────────────────────────────

  validate(id: string, decision: ValidationDecision): Observable<{
    status: string; blockchain_hash?: string; message: string;
  }> {
    return this.api.post(`/parcelles/${id}/valider/`, decision).pipe(
      tap(() => {
        // Mettre à jour le signal localement (optimistic update)
        this._parcels.update(parcels =>
          parcels.map(p => p.id === id
            ? { ...p, status: decision.decision === 'approve' ? 'validated' : 'rejected' as any }
            : p
          )
        );
      }),
    );
  }

  reject(id: string, reason: string): Observable<{ message: string }> {
    return this.validate(id, { decision: 'reject', reason });
  }

  deleteParcel(id: string): Observable<void> {
    return this.api.delete<void>(`/parcelles/${id}/`).pipe(
      tap(() => this._parcels.update(ps => ps.filter(p => p.id !== id))),
    );
  }

  verifyCertificate(hash: string): Observable<{
    valide: boolean; parcelle?: string; date_validation?: string;
  }> {
    return this.api.get(`/certificats/verifier/`, { hash });
  }

  // ──────────────────────────────────────────────
  // STATISTIQUES
  // ──────────────────────────────────────────────

  getParcelStats(): Observable<{
    pending: number; certified: number; rejected: number; total: number;
  }> {
    return this.api.get('/parcelles/stats/');
  }
}


// ═══════════════════════════════════════════════════════════════