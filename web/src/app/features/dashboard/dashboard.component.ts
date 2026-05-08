// ═══════════════════════════════════════════════════════════════
// src/app/features/dashboard/dashboard.component.ts
// ═══════════════════════════════════════════════════════════════

import {
  Component, inject, OnInit, signal, computed, ChangeDetectionStrategy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DashboardService } from './dashboard.service';
import { DashboardStats, AuditLog, Parcel } from '@core/models';

@Component({
  selector:         'app-dashboard',
  standalone:       true,
  changeDetection:  ChangeDetectionStrategy.OnPush,
  imports:          [CommonModule, RouterLink],
  template: `
    <div class="dashboard">

      <!-- ─── Header page ─── -->
      <div class="page-header">
        <h1 class="page-title">Tableau de bord</h1>
        <p class="page-subtitle">Vue d'ensemble de Sen_parcelle</p>
      </div>

      <!-- ─── Stats cards ─── -->
      <div class="stats-grid" *ngIf="stats()">
        <div class="stat-card stat-card--amber">
          <div class="stat-card__header">
            <span class="stat-card__icon">⏳</span>
            <span class="stat-card__trend">↑</span>
          </div>
          <div class="stat-card__value">{{ stats()!.parcels.pending }}</div>
          <div class="stat-card__label">Parcelles en attente</div>
          <a routerLink="/validation" class="stat-card__link">Valider →</a>
        </div>

        <div class="stat-card stat-card--green">
          <div class="stat-card__header">
            <span class="stat-card__icon">✅</span>
          </div>
          <div class="stat-card__value">{{ stats()!.parcels.certified }}</div>
          <div class="stat-card__label">Parcelles certifiées</div>
          <a routerLink="/blockchain" class="stat-card__link">Voir blockchain →</a>
        </div>

        <div class="stat-card stat-card--blue">
          <div class="stat-card__header">
            <span class="stat-card__icon">👤</span>
          </div>
          <div class="stat-card__value">{{ stats()!.users.total }}</div>
          <div class="stat-card__label">Utilisateurs inscrits</div>
          <div class="stat-card__sub">{{ stats()!.users.pending_kyc }} KYC en attente</div>
        </div>

        <div class="stat-card stat-card--purple">
          <div class="stat-card__header">
            <span class="stat-card__icon">🔗</span>
          </div>
          <div class="stat-card__value">{{ stats()!.blockchain.total_tx }}</div>
          <div class="stat-card__label">Transactions blockchain</div>
          <a routerLink="/blockchain" class="stat-card__link">Explorer →</a>
        </div>
      </div>

      <!-- ─── Skeleton loading ─── -->
      <div class="stats-grid" *ngIf="isLoading()">
        <div class="stat-card skeleton" *ngFor="let _ of [1,2,3,4]"></div>
      </div>

      <!-- ─── Main grid ─── -->
      <div class="dashboard-grid">

        <!-- Parcelles récentes -->
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h2 class="dashboard-card__title">Parcelles récentes</h2>
            <a routerLink="/parcelles" class="dashboard-card__link">Voir tout</a>
          </div>
          <div class="dashboard-card__body">
            <div class="parcel-item" *ngFor="let p of recentParcels()">
              <div class="parcel-item__info">
                <span class="parcel-item__title">{{ p.titre }}</span>
                <span class="parcel-item__region">{{ p.region }}</span>
              </div>
              <div class="parcel-item__right">
                <span class="badge" [ngClass]="getStatusClass(p.status)">
                  {{ getStatusLabel(p.status) }}
                </span>
                <span class="parcel-item__price">{{ formatPrice(p.price) }}</span>
              </div>
            </div>
            <div class="empty-state" *ngIf="!recentParcels().length && !isLoading()">
              Aucune parcelle récente
            </div>
          </div>
        </div>

        <!-- Activité récente -->
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h2 class="dashboard-card__title">Activité récente</h2>
          </div>
          <div class="dashboard-card__body">
            <div class="activity-item" *ngFor="let log of recentActivity()">
              <div class="activity-item__dot"
                [class.activity-item__dot--green]="log.action.includes('success') || log.action.includes('certified')"
                [class.activity-item__dot--red]="log.action.includes('failed') || log.action.includes('reject')"
                [class.activity-item__dot--amber]="log.action.includes('pending') || log.action.includes('submitted')">
              </div>
              <div class="activity-item__content">
                <span class="activity-item__action">{{ formatAction(log.action) }}</span>
                <span class="activity-item__time">{{ formatTime(log.created_at) }}</span>
              </div>
            </div>
            <div class="empty-state" *ngIf="!recentActivity().length && !isLoading()">
              Aucune activité récente
            </div>
          </div>
        </div>

      </div>
    </div>
  `,
  styles: [`
    .dashboard { max-width: 1400px; }

    .page-header { margin-bottom: 24px; }
    .page-title  { font-size: 24px; font-weight: 800; color: #1E293B; margin: 0 0 4px; }
    .page-subtitle { font-size: 14px; color: #64748B; margin: 0; }

    /* ── Stats Grid ── */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 28px;
    }
    @media (max-width: 1100px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px)  { .stats-grid { grid-template-columns: 1fr; } }

    .stat-card {
      background: #fff;
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
      border-top: 4px solid transparent;
    }
    .stat-card--amber  { border-top-color: #D97706; }
    .stat-card--green  { border-top-color: #16A34A; }
    .stat-card--blue   { border-top-color: #2563EB; }
    .stat-card--purple { border-top-color: #7C3AED; }

    .stat-card__header  { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
    .stat-card__icon    { font-size: 24px; }
    .stat-card__trend   { font-size: 12px; color: #16A34A; font-weight: 600; }
    .stat-card__value   { font-size: 32px; font-weight: 900; color: #1E293B; margin: 4px 0; }
    .stat-card__label   { font-size: 13px; color: #64748B; font-weight: 600; margin-bottom: 8px; }
    .stat-card__sub     { font-size: 12px; color: #D97706; }
    .stat-card__link    { font-size: 12px; color: #16A34A; font-weight: 600; text-decoration: none; }

    .skeleton {
      height: 130px;
      background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      border-top: none !important;
    }
    @keyframes shimmer { to { background-position: -200% 0; } }

    /* ── Dashboard Grid ── */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    @media (max-width: 900px) { .dashboard-grid { grid-template-columns: 1fr; } }

    .dashboard-card {
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
      overflow: hidden;
    }
    .dashboard-card__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid #F1F5F9;
    }
    .dashboard-card__title { font-size: 15px; font-weight: 700; margin: 0; color: #1E293B; }
    .dashboard-card__link  { font-size: 12px; color: #16A34A; font-weight: 600; text-decoration: none; }
    .dashboard-card__body  { padding: 8px 0; }

    /* ── Parcel items ── */
    .parcel-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 20px;
      border-bottom: 1px solid #F8FAFC;
      transition: .15s;
    }
    .parcel-item:hover { background: #F8FAFC; }
    .parcel-item__info  { display: flex; flex-direction: column; gap: 2px; }
    .parcel-item__title  { font-size: 13px; font-weight: 600; color: #1E293B; }
    .parcel-item__region { font-size: 12px; color: #64748B; }
    .parcel-item__right  { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
    .parcel-item__price  { font-size: 13px; font-weight: 700; color: #14532D; }

    /* ── Badges ── */
    .badge {
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge--pending   { background: #FEF3C7; color: #D97706; }
    .badge--certified { background: #DCFCE7; color: #16A34A; }
    .badge--rejected  { background: #FEE2E2; color: #DC2626; }
    .badge--sold      { background: #DBEAFE; color: #2563EB; }

    /* ── Activity ── */
    .activity-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 20px;
      border-bottom: 1px solid #F8FAFC;
    }
    .activity-item__dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: #94A3B8;
      margin-top: 4px;
      flex-shrink: 0;
    }
    .activity-item__dot--green  { background: #16A34A; }
    .activity-item__dot--red    { background: #DC2626; }
    .activity-item__dot--amber  { background: #D97706; }
    .activity-item__content     { flex: 1; }
    .activity-item__action      { display: block; font-size: 13px; color: #1E293B; font-weight: 500; }
    .activity-item__time        { font-size: 11px; color: #94A3B8; margin-top: 2px; }

    .empty-state {
      text-align: center;
      padding: 24px;
      color: #94A3B8;
      font-size: 13px;
    }
  `],
})
export class DashboardComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);

  readonly stats          = this.dashboardService.stats;
  readonly isLoading      = this.dashboardService.isLoading;
  readonly recentParcels  = signal<Parcel[]>([]);
  readonly recentActivity = signal<AuditLog[]>([]);

  ngOnInit(): void {
    this.dashboardService.loadDashboard().subscribe();
    this.dashboardService.getRecentParcels().subscribe(p => this.recentParcels.set(p));
    this.dashboardService.getRecentActivity().subscribe(a => this.recentActivity.set(a));
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = {
      pending: 'badge--pending', certified: 'badge--certified',
      rejected: 'badge--rejected', sold: 'badge--sold',
      validated: 'badge--certified',
    };
    return `badge ${map[status] ?? 'badge--pending'}`;
  }

  getStatusLabel(status: string): string {
    const map: Record<string, string> = {
      pending: '⏳ En attente', validated: '✓ Validée',
      certified: '✓ Certifiée', rejected: '✗ Rejetée', sold: '💰 Vendue',
    };
    return map[status] ?? status;
  }

  formatPrice(price: number): string {
    if (price >= 1_000_000_000) return `${(price / 1_000_000_000).toFixed(1)}Md FCFA`;
    if (price >= 1_000_000)    return `${(price / 1_000_000).toFixed(0)}M FCFA`;
    return `${price.toLocaleString()} FCFA`;
  }

  formatAction(action: string): string {
    const map: Record<string, string> = {
      login_success:    '✅ Connexion réussie',
      login_failed:     '❌ Échec de connexion',
      parcel_submitted: '📋 Nouvelle parcelle soumise',
      parcel_certified: '🔗 Parcelle certifiée blockchain',
      parcel_rejected:  '✗ Parcelle rejetée',
      kyc_submitted:    '🪪 KYC soumis',
      kyc_approved:     '✅ KYC approuvé',
    };
    return map[action] ?? action.replace(/_/g, ' ');
  }

  formatTime(dateStr: string): string {
    const date = new Date(dateStr);
    const diff = Date.now() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)   return 'à l\'instant';
    if (mins < 60)  return `il y a ${mins}min`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24)   return `il y a ${hrs}h`;
    return date.toLocaleDateString('fr-SN');
  }
}