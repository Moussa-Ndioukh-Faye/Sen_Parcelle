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
      <div class="page-header">
        <div>
          <h1 class="page-title">Tableau de bord</h1>
          <p class="page-subtitle">Vue d'ensemble de Sen_parcelle</p>
        </div>
        <button class="btn btn--outline btn--sm" (click)="refresh()">
          <span class="material-icons">refresh</span> Actualiser
        </button>
      </div>

      @if (isLoading()) {
        <div class="stats-grid">
          @for (_ of [1,2,3,4]; track _) {
            <div class="stat-card stat-card--skeleton">
              <div class="skeleton" style="width:40px;height:40px;border-radius:12px"></div>
              <div class="skeleton" style="width:60%;height:28px;margin-top:12px"></div>
              <div class="skeleton" style="width:40%;height:14px;margin-top:8px"></div>
            </div>
          }
        </div>
      }

      @if (stats(); as s) {
        <div class="stats-grid fade-in">
          <div class="stat-card stat-card--amber">
            <div class="stat-card__header">
              <div class="stat-card__icon stat-card__icon--amber">
                <span class="material-icons">hourglass_empty</span>
              </div>
              <span class="stat-card__trend">+{{ s.parcels.pending > 0 ? 3 : 0 }}%</span>
            </div>
            <div class="stat-card__value">{{ s.parcels.pending }}</div>
            <div class="stat-card__label">Parcelles en attente</div>
            <a routerLink="/validation" class="stat-card__link">Valider <span class="material-icons">arrow_forward</span></a>
          </div>

          <div class="stat-card stat-card--green">
            <div class="stat-card__header">
              <div class="stat-card__icon stat-card__icon--green">
                <span class="material-icons">check_circle</span>
              </div>
              <span class="stat-card__trend">+{{ s.parcels.certified > 0 ? 12 : 0 }}%</span>
            </div>
            <div class="stat-card__value">{{ s.parcels.certified }}</div>
            <div class="stat-card__label">Parcelles certifiées</div>
            <a routerLink="/blockchain" class="stat-card__link">Voir blockchain <span class="material-icons">arrow_forward</span></a>
          </div>

          <div class="stat-card stat-card--blue">
            <div class="stat-card__header">
              <div class="stat-card__icon stat-card__icon--blue">
                <span class="material-icons">people</span>
              </div>
            </div>
            <div class="stat-card__value">{{ s.users.total }}</div>
            <div class="stat-card__label">Utilisateurs inscrits</div>
            <div class="stat-card__sub">{{ s.users.pending_kyc }} KYC en attente</div>
          </div>

          <div class="stat-card stat-card--purple">
            <div class="stat-card__header">
              <div class="stat-card__icon stat-card__icon--purple">
                <span class="material-icons">link</span>
              </div>
            </div>
            <div class="stat-card__value">{{ s.blockchain.total_tx }}</div>
            <div class="stat-card__label">Transactions blockchain</div>
            <a routerLink="/blockchain" class="stat-card__link">Explorer <span class="material-icons">arrow_forward</span></a>
          </div>
        </div>
      }

      <div class="dashboard-grid">
        <div class="dashboard-card fade-in">
          <div class="dashboard-card__header">
            <h2 class="dashboard-card__title">
              <span class="material-icons">home</span> Parcelles récentes
            </h2>
            <a routerLink="/parcelles" class="dashboard-card__link">Voir tout</a>
          </div>
          <div class="dashboard-card__body">
            @for (p of recentParcels(); track p.id) {
              <div class="parcel-item">
                <div class="parcel-item__info">
                  <span class="parcel-item__title">{{ p.titre }}</span>
                  <span class="parcel-item__region">
                    <span class="material-icons">location_on</span> {{ p.region }}
                  </span>
                </div>
                <div class="parcel-item__right">
                  <span class="badge" [ngClass]="getStatusClass(p.status)">
                    <span class="material-icons" style="font-size:12px">{{ getStatusIcon(p.status) }}</span>
                    {{ getStatusLabel(p.status) }}
                  </span>
                  <span class="parcel-item__price">{{ formatPrix(p.prix) }}</span>
                </div>
              </div>
            }
            @empty {
              <div class="empty-state">
                <span class="material-icons">inbox</span>
                <span>Aucune parcelle récente</span>
              </div>
            }
          </div>
        </div>

        <div class="dashboard-card fade-in">
          <div class="dashboard-card__header">
            <h2 class="dashboard-card__title">
              <span class="material-icons">timeline</span> Activité récente
            </h2>
          </div>
          <div class="dashboard-card__body">
            <div class="activity-feed">
              @for (log of recentActivity(); track log.id) {
                <div class="activity-item">
                  <div class="activity-item__line">
                    <div class="activity-item__dot"
                      [class.dot--green]="log.action.includes('success') || log.action.includes('certified')"
                      [class.dot--red]="log.action.includes('failed') || log.action.includes('reject')"
                      [class.dot--amber]="log.action.includes('pending') || log.action.includes('submitted')">
                    </div>
                    @if (!$last) { <div class="activity-item__connector"></div> }
                  </div>
                  <div class="activity-item__content">
                    <span class="activity-item__action">
                      <span class="material-icons" style="font-size:14px;vertical-align:middle">{{ getActionIcon(log.action) }}</span>
                      {{ getActionLabel(log.action) }}
                    </span>
                    <span class="activity-item__time">{{ formatTime(log.created_at) }}</span>
                  </div>
                </div>
              }
              @empty {
                <div class="empty-state">
                  <span class="material-icons">inbox</span>
                  <span>Aucune activité récente</span>
                </div>
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard { max-width: 1400px; }

    .page-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .page-title  { font-size: 24px; font-weight: 800; color: var(--slate-900); margin: 0 0 4px; letter-spacing: -0.5px; }
    .page-subtitle { font-size: 14px; color: var(--slate-500); margin: 0; }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin-bottom: 28px;
    }
    @media (max-width: 1100px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px)  { .stats-grid { grid-template-columns: 1fr; } }

    .stat-card {
      background: var(--white);
      border-radius: var(--radius-lg);
      padding: 22px;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s var(--ease-out);
      position: relative;
      overflow: hidden;
    }
    .stat-card:hover {
      box-shadow: var(--shadow-lg);
      transform: translateY(-2px);
    }
    .stat-card--skeleton { padding: 22px; }
    .stat-card--amber  { --accent: var(--amber-500); }
    .stat-card--green  { --accent: var(--green-500); }
    .stat-card--blue   { --accent: var(--blue-600); }
    .stat-card--purple { --accent: var(--purple-600); }

    .stat-card__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }
    .stat-card__icon {
      width: 44px; height: 44px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
    }
    .stat-card__icon--amber  { background: var(--amber-50); color: var(--amber-600); }
    .stat-card__icon--green  { background: var(--green-50); color: var(--green-600); }
    .stat-card__icon--blue   { background: var(--blue-50); color: var(--blue-600); }
    .stat-card__icon--purple { background: var(--purple-50); color: var(--purple-600); }

    .stat-card__trend {
      font-size: 12px;
      color: var(--green-600);
      font-weight: 600;
      background: var(--green-50);
      padding: 2px 8px;
      border-radius: var(--radius-full);
    }
    .stat-card__value {
      font-size: 32px;
      font-weight: 900;
      color: var(--slate-900);
      margin: 0 0 4px;
      letter-spacing: -1px;
    }
    .stat-card__label {
      font-size: 13px;
      color: var(--slate-500);
      font-weight: 500;
      margin-bottom: 10px;
    }
    .stat-card__sub {
      font-size: 12px;
      color: var(--amber-600);
      font-weight: 500;
    }
    .stat-card__link {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: var(--accent, var(--green-600));
      font-weight: 600;
      text-decoration: none;
      transition: gap 0.15s;
    }
    .stat-card__link:hover { gap: 8px; }
    .stat-card__link .material-icons { font-size: 14px; }

    .dashboard-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    @media (max-width: 900px) { .dashboard-grid { grid-template-columns: 1fr; } }

    .dashboard-card {
      background: var(--white);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      transition: box-shadow 0.2s var(--ease-out);
    }
    .dashboard-card:hover { box-shadow: var(--shadow-md); }
    .dashboard-card__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 22px;
      border-bottom: 1px solid var(--slate-100);
    }
    .dashboard-card__title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 700;
      margin: 0;
      color: var(--slate-900);
    }
    .dashboard-card__title .material-icons { font-size: 18px; color: var(--green-600); }
    .dashboard-card__link {
      font-size: 12px;
      color: var(--green-600);
      font-weight: 600;
      text-decoration: none;
      transition: color .15s;
    }
    .dashboard-card__link:hover { color: var(--green-700); }
    .dashboard-card__body { padding: 4px 0; }

    .parcel-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 22px;
      border-bottom: 1px solid var(--slate-50);
      transition: all 0.15s;
    }
    .parcel-item:hover { background: var(--slate-50); padding-left: 26px; }
    .parcel-item:last-child { border-bottom: none; }
    .parcel-item__info  { display: flex; flex-direction: column; gap: 3px; }
    .parcel-item__title  { font-size: 13px; font-weight: 600; color: var(--slate-900); }
    .parcel-item__region {
      display: flex;
      align-items: center;
      gap: 3px;
      font-size: 12px;
      color: var(--slate-500);
    }
    .parcel-item__region .material-icons { font-size: 13px; }
    .parcel-item__right  { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; }
    .parcel-item__price  { font-size: 13px; font-weight: 700; color: var(--green-800); }

    .activity-feed { padding: 8px 0; }
    .activity-item {
      display: flex;
      gap: 12px;
      padding: 0 22px;
    }
    .activity-item__line {
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 12px;
      flex-shrink: 0;
      padding-top: 3px;
    }
    .activity-item__dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      background: var(--slate-300);
      flex-shrink: 0;
      border: 2px solid var(--slate-100);
    }
    .activity-item__dot.dot--green  { background: var(--green-500); border-color: var(--green-100); }
    .activity-item__dot.dot--red    { background: var(--red-500); border-color: var(--red-100); }
    .activity-item__dot.dot--amber  { background: var(--amber-500); border-color: var(--amber-100); }

    .activity-item__connector {
      width: 2px;
      flex: 1;
      background: var(--slate-100);
      margin: 4px 0;
    }

    .activity-item__content {
      flex: 1;
      padding-bottom: 16px;
    }
    .activity-item__action {
      display: block;
      font-size: 13px;
      color: var(--slate-900);
      font-weight: 500;
    }
    .activity-item__time {
      display: block;
      font-size: 11px;
      color: var(--slate-400);
      margin-top: 3px;
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 32px;
      color: var(--slate-400);
      font-size: 13px;
    }
    .empty-state .material-icons { font-size: 32px; opacity: 0.5; }
  `],
})
export class DashboardComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);

  readonly stats          = this.dashboardService.stats;
  readonly isLoading      = this.dashboardService.isLoading;
  readonly recentParcels  = signal<Parcel[]>([]);
  readonly recentActivity = signal<AuditLog[]>([]);

  ngOnInit(): void {
    this.loadData();
  }

  private loadData(): void {
    this.dashboardService.loadDashboard().subscribe();
    this.dashboardService.getRecentParcels().subscribe(p => this.recentParcels.set(p));
    this.dashboardService.getRecentActivity().subscribe(a => this.recentActivity.set(a));
  }

  refresh(): void {
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

  getStatusIcon(status: string): string {
    const map: Record<string, string> = {
      pending: 'hourglass_empty', validated: 'check_circle',
      certified: 'verified', rejected: 'close', sold: 'paid',
    };
    return map[status] ?? 'help_outline';
  }
  getStatusLabel(status: string): string {
    const map: Record<string, string> = {
      pending: 'En attente', validated: 'Validée',
      certified: 'Certifiée', rejected: 'Rejetée', sold: 'Vendue',
    };
    return map[status] ?? status;
  }

  formatPrix(prix: number): string {
    if (prix >= 1_000_000_000) return `${(prix / 1_000_000_000).toFixed(1)}Md FCFA`;
    if (prix >= 1_000_000)    return `${(prix / 1_000_000).toFixed(0)}M FCFA`;
    return `${prix.toLocaleString()} FCFA`;
  }

  getActionIcon(action: string): string {
    const map: Record<string, string> = {
      login_success:    'login',
      login_failed:     'cancel',
      parcel_submitted: 'note_add',
      parcel_certified: 'link',
      parcel_rejected:  'close',
      kyc_submitted:    'badge',
      kyc_approved:     'check_circle',
    };
    return map[action] ?? 'help_outline';
  }
  getActionLabel(action: string): string {
    const map: Record<string, string> = {
      login_success:    'Connexion réussie',
      login_failed:     'Échec de connexion',
      parcel_submitted: 'Nouvelle parcelle soumise',
      parcel_certified: 'Parcelle certifiée blockchain',
      parcel_rejected:  'Parcelle rejetée',
      kyc_submitted:    'KYC soumis',
      kyc_approved:     'KYC approuvé',
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
