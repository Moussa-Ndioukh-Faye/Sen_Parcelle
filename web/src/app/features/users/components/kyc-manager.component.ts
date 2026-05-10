// src/app/features/users/components/kyc-manager.component.ts
// ═══════════════════════════════════════════════════════════════

import {
  Component, inject, OnInit, signal, ChangeDetectionStrategy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { UsersService } from '../services/users.service';
import { User } from '@core/models';

@Component({
  selector:        'app-kyc-manager',
  standalone:      true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports:         [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">Gestion KYC</h1>
        <span class="page-header__badge">{{ pending().length }} en attente</span>
      </div>

      <!-- ─── Tabs ─── -->
      <div class="tabs">
        <button class="tab" [class.tab--active]="activeTab() === 'pending'"
          (click)="setTab('pending')"><span class="material-icons" style="font-size:14px;vertical-align:middle">hourglass_empty</span> En attente ({{ pending().length }})</button>
        <button class="tab" [class.tab--active]="activeTab() === 'verified'"
          (click)="setTab('verified')"><span class="material-icons" style="font-size:14px;vertical-align:middle">check_circle</span> Vérifiés</button>
        <button class="tab" [class.tab--active]="activeTab() === 'rejected'"
          (click)="setTab('rejected')"><span class="material-icons" style="font-size:14px;vertical-align:middle">close</span> Rejetés</button>
      </div>

      <!-- ─── Liste KYC ─── -->
      <div class="kyc-list">
        <div class="kyc-card" *ngFor="let u of displayedUsers()">
          <div class="kyc-card__avatar" [style.background]="getAvatarColor(u.nom)">
            {{ u.nom[0].toUpperCase() }}
          </div>
          <div class="kyc-card__info">
            <div class="kyc-card__name">{{ u.nom }}</div>
            <div class="kyc-card__email">{{ u.email }}</div>
            <div class="kyc-card__phone">{{ u.telephone }}</div>
            <div class="kyc-card__date">Inscrit le {{ formatDate(u.created_at) }}</div>
          </div>
          <div class="kyc-card__status">
            <span class="badge" [ngClass]="getKYCClass(u.kyc_status)">
              <span class="material-icons" style="font-size:12px;vertical-align:middle">{{ getKYCIcon(u.kyc_status) }}</span>
              {{ getKYCLabel(u.kyc_status) }}
            </span>
            <span class="role-badge">{{ u.role }}</span>
          </div>
          <div class="kyc-card__actions" *ngIf="u.kyc_status === 'pending'">
            <button class="btn btn--sm btn--success"
              [disabled]="processingId() === u.id"
              (click)="approve(u)">
              <span *ngIf="processingId() === u.id">...</span>
              <span *ngIf="processingId() !== u.id"><span class="material-icons" style="font-size:14px;vertical-align:middle">check_circle</span> Approuver</span>
            </button>
            <button class="btn btn--sm btn--danger" (click)="openReject(u)">
              <span class="material-icons" style="font-size:14px;vertical-align:middle">close</span> Rejeter
            </button>
          </div>
          <div class="kyc-card__actions" *ngIf="u.kyc_status !== 'pending'">
            <span class="kyc-done" *ngIf="u.kyc_status === 'verified'"><span class="material-icons" style="font-size:14px;vertical-align:middle">check_circle</span> Approuvé</span>
            <span class="kyc-done kyc-done--red" *ngIf="u.kyc_status === 'rejected'"><span class="material-icons" style="font-size:14px;vertical-align:middle">close</span> Rejeté</span>
          </div>
        </div>

        <div class="empty-state" *ngIf="!displayedUsers().length">
          <span class="material-icons" style="font-size:32px">search</span>
          <p>Aucun utilisateur dans cette catégorie</p>
        </div>
      </div>

      <!-- ─── Modal rejet ─── -->
      <div class="modal-overlay" *ngIf="rejectUser()" (click)="closeReject()">
        <div class="modal" (click)="$event.stopPropagation()">
          <div class="modal__header">
            <h3>Rejeter le KYC de {{ rejectUser()?.nom }}</h3>
            <button class="modal__close" (click)="closeReject()">×</button>
          </div>
          <div class="modal__body">
            <textarea [(ngModel)]="rejectReason"
              class="modal__textarea" rows="3"
              placeholder="Motif du rejet...">
            </textarea>
          </div>
          <div class="modal__footer">
            <button class="btn btn--outline" (click)="closeReject()">Annuler</button>
            <button class="btn btn--danger" (click)="confirmReject()">Confirmer</button>
          </div>
        </div>
      </div>

      <div class="toast" [class.toast--visible]="toast()">{{ toast() }}</div>
    </div>
  `,
  styles: [`
    .page-header { display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }
    .page-title  { margin: 0; font-size: 22px; font-weight: 800; color: #1E293B; }
    .page-header__badge {
      background: #D97706; color: #fff;
      padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 700;
    }

    .tabs { display: flex; gap: 8px; margin-bottom: 20px; }
    .tab {
      padding: 8px 18px; border-radius: 10px; border: 1.5px solid #E2E8F0;
      background: #fff; font-size: 13px; font-weight: 600; cursor: pointer;
      color: #64748B; transition: .15s;
    }
    .tab:hover { border-color: #16A34A; color: #16A34A; }
    .tab--active { background: #16A34A; border-color: #16A34A; color: #fff; }

    .kyc-list { display: flex; flex-direction: column; gap: 10px; }
    .kyc-card {
      background: #fff; border-radius: 14px; padding: 16px 20px;
      display: flex; align-items: center; gap: 16px;
      box-shadow: 0 2px 10px rgba(0,0,0,.05);
      transition: .15s;
    }
    .kyc-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); }
    .kyc-card__avatar {
      width: 48px; height: 48px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; font-weight: 800; color: #fff; flex-shrink: 0;
    }
    .kyc-card__info { flex: 1; }
    .kyc-card__name  { font-size: 15px; font-weight: 700; color: #1E293B; }
    .kyc-card__email { font-size: 12px; color: #64748B; margin-top: 2px; }
    .kyc-card__phone { font-size: 12px; color: #64748B; }
    .kyc-card__date  { font-size: 11px; color: #94A3B8; margin-top: 4px; }
    .kyc-card__status { display: flex; flex-direction: column; gap: 6px; align-items: flex-end; }
    .kyc-card__actions { display: flex; gap: 8px; flex-shrink: 0; }
    .kyc-done { font-size: 13px; font-weight: 600; color: #16A34A; }
    .kyc-done--red { color: #DC2626; }

    .badge { padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .badge--pending  { background: #FEF3C7; color: #D97706; }
    .badge--verified { background: #DCFCE7; color: #16A34A; }
    .badge--rejected { background: #FEE2E2; color: #DC2626; }
    .role-badge {
      font-size: 10px; background: #F1F5F9; color: #64748B;
      padding: 2px 8px; border-radius: 10px; font-weight: 600;
      text-transform: capitalize;
    }

    .btn { padding: 10px 18px; border-radius: 10px; border: none;
      font-size: 14px; font-weight: 600; cursor: pointer; transition: .15s; }
    .btn:disabled { opacity: .5; cursor: not-allowed; }
    .btn--sm      { padding: 7px 14px; font-size: 12px; }
    .btn--success { background: #16A34A; color: #fff; }
    .btn--success:hover:not(:disabled) { background: #14532D; }
    .btn--danger  { background: #DC2626; color: #fff; }
    .btn--outline { background: transparent; border: 1.5px solid #E2E8F0; color: #64748B; }

    .empty-state {
      text-align: center; padding: 40px; color: #64748B; font-size: 32px;
      background: #fff; border-radius: 14px;
    }
    .empty-state p { font-size: 14px; margin: 8px 0 0; }

    .modal-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,.5);
      display: flex; align-items: center; justify-content: center; z-index: 1000;
    }
    .modal { background: #fff; border-radius: 16px; width: 420px; max-width: 90vw; }
    .modal__header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 18px 20px; border-bottom: 1px solid #F1F5F9;
    }
    .modal__header h3 { margin: 0; font-size: 15px; }
    .modal__close { background: none; border: none; font-size: 20px; cursor: pointer; }
    .modal__body    { padding: 18px 20px; }
    .modal__footer  {
      display: flex; justify-content: flex-end; gap: 10px;
      padding: 14px 20px; border-top: 1px solid #F1F5F9;
    }
    .modal__textarea {
      width: 100%; padding: 10px 14px; border: 1.5px solid #E2E8F0;
      border-radius: 10px; font-size: 13px; resize: vertical;
      outline: none; font-family: inherit; box-sizing: border-box;
    }
    .modal__textarea:focus { border-color: #16A34A; }

    .toast {
      position: fixed; bottom: 24px; right: 24px;
      background: #16A34A; color: #fff;
      padding: 12px 20px; border-radius: 12px; font-size: 14px; font-weight: 600;
      transform: translateY(80px); opacity: 0; transition: all .3s ease;
    }
    .toast--visible { transform: translateY(0); opacity: 1; }
  `],
})
export class KYCManagerComponent implements OnInit {
  private readonly usersService = inject(UsersService);

  allUsers     = signal<User[]>([]);
  activeTab    = signal<'pending' | 'verified' | 'rejected'>('pending');
  processingId = signal<string | null>(null);
  rejectUser   = signal<User | null>(null);
  rejectReason = '';
  toast        = signal<string | null>(null);

  pending  = signal<User[]>([]);
  verified = signal<User[]>([]);
  rejected = signal<User[]>([]);

  displayedUsers = () => {
    const tab = this.activeTab();
    if (tab === 'pending')  return this.pending();
    if (tab === 'verified') return this.verified();
    return this.rejected();
  };

  ngOnInit(): void {
    this.usersService.fetchUsers().subscribe(r => {
      this.allUsers.set(r.results);
      this.pending.set(r.results.filter(u => u.kyc_status === 'pending'));
      this.verified.set(r.results.filter(u => u.kyc_status === 'verified'));
      this.rejected.set(r.results.filter(u => u.kyc_status === 'rejected'));
    });
  }

  setTab(tab: 'pending' | 'verified' | 'rejected'): void { this.activeTab.set(tab); }

  approve(user: User): void {
    this.processingId.set(user.id);
    this.usersService.approveKYC(user.id).subscribe({
      next: () => {
        this.pending.update(us => us.filter(u => u.id !== user.id));
        this.verified.update(us => [...us, { ...user, kyc_status: 'verified' }]);
        this.processingId.set(null);
        this.showToast(`KYC de ${user.nom} approuvé. SMS envoyé.`);
      },
      error: () => this.processingId.set(null),
    });
  }

  openReject(user: User): void  { this.rejectUser.set(user); this.rejectReason = ''; }
  closeReject(): void           { this.rejectUser.set(null); }

  confirmReject(): void {
    const user = this.rejectUser();
    if (!user) return;
    this.usersService.rejectKYC(user.id, this.rejectReason).subscribe({
      next: () => {
        this.pending.update(us => us.filter(u => u.id !== user.id));
        this.rejected.update(us => [...us, { ...user, kyc_status: 'rejected' }]);
        this.closeReject();
        this.showToast(`KYC de ${user.nom} rejeté.`);
      },
    });
  }

  private showToast(msg: string): void {
    this.toast.set(msg);
    setTimeout(() => this.toast.set(null), 3500);
  }

  getAvatarColor(nom: string): string {
    const colors = ['#16A34A','#2563EB','#7C3AED','#D97706','#DC2626','#0891B2'];
    return colors[nom.charCodeAt(0) % colors.length];
  }
  getKYCClass(status: string): string {
    const m: Record<string, string> = {
      pending: 'badge--pending', verified: 'badge--verified', rejected: 'badge--rejected',
    };
    return `badge ${m[status] ?? ''}`;
  }
  getKYCIcon(status: string): string {
    const m: Record<string, string> = {
      pending: 'hourglass_empty', verified: 'check_circle', rejected: 'close',
    };
    return m[status] ?? 'help_outline';
  }
  getKYCLabel(status: string): string {
    const m: Record<string, string> = {
      pending: 'En attente', verified: 'Vérifié', rejected: 'Rejeté',
    };
    return m[status] ?? status;
  }
  formatDate(d: string): string {
    return new Date(d).toLocaleDateString('fr-SN', { day: '2-digit', month: 'short', year: 'numeric' });
  }
}


// ═══════════════════════════════════════════════════════════════