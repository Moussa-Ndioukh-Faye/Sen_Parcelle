// src/app/features/dashboard/dashboard.service.ts
// ═══════════════════════════════════════════════════════════════

import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap, forkJoin, map } from 'rxjs';
import { ApiService } from '@core/services/api.service';
import { DashboardStats, AuditLog, Parcel, User } from '@core/models';

@Injectable({ providedIn: 'root' })
export class DashboardService {

  private readonly api = inject(ApiService);

  private _stats     = signal<DashboardStats | null>(null);
  private _isLoading = signal(false);

  readonly stats     = this._stats.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();

  loadDashboard(): Observable<DashboardStats> {
    this._isLoading.set(true);

    // Appels parallèles pour les stats
    return forkJoin({
      pendingParcels: this.api.get<{ count: number }>('/parcelles/', { status: 'pending' }),
      certifiedParcels: this.api.get<{ count: number }>('/parcelles/', { status: 'certified' }),
      pendingKYC: this.api.get<{ count: number }>('/utilisateurs/', { kyc_status: 'pending' }),
      totalUsers: this.api.get<{ count: number }>('/utilisateurs/'),
    }).pipe(
      map(data => ({
        users: {
          total:       data.totalUsers.count,
          pending_kyc: data.pendingKYC.count,
          new_today:   0,
        },
        parcels: {
          total:     data.pendingParcels.count + data.certifiedParcels.count,
          pending:   data.pendingParcels.count,
          certified: data.certifiedParcels.count,
          rejected:  0,
        },
        transactions: {
          total: 0, completed: 0, volume_fcfa: 0,
        },
        blockchain: {
          total_tx: data.certifiedParcels.count,
          last_block: 0,
        },
      } as DashboardStats)),
      tap(stats => {
        this._stats.set(stats);
        this._isLoading.set(false);
      }),
    );
  }

  getRecentActivity(): Observable<AuditLog[]> {
    return this.api.get<AuditLog[]>('/audit/recent/');
  }

  getRecentParcels(): Observable<Parcel[]> {
    return this.api.get<{ results: Parcel[] }>('/parcelles/', { page_size: 5 })
      .pipe(map(r => r.results));
  }
}