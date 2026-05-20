// ═══════════════════════════════════════════════════════════════
// src/app/features/parcels/components/validation.component.ts
// Admin : valider / rejeter les parcelles en attente
// ═══════════════════════════════════════════════════════════════

import {
  Component, inject, OnInit, signal, ChangeDetectionStrategy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ParcelsService } from '../services/parcels.service';
import { Parcel } from '@core/models';

@Component({
  selector:        'app-validation',
  standalone:      true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports:         [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">Validation des parcelles</h1>
        <div class="page-header__badge">
          {{ parcelsService.pendingCount() }} en attente
        </div>
      </div>

      <!-- ─── Loading ─── -->
      <div class="loading" *ngIf="parcelsService.isLoading()">
        <div class="spinner"></div>
        <span>Chargement des parcelles...</span>
      </div>

      <!-- ─── Empty ─── -->
      <div class="empty-state" *ngIf="!parcelsService.isLoading() && !pending().length">
        <span class="empty-state__icon material-icons">check_circle</span>
        <h3>Aucune parcelle en attente</h3>
        <p>Toutes les parcelles ont été traitées.</p>
      </div>

      <!-- ─── Table ─── -->
      <div class="table-card" *ngIf="pending().length">
        <table class="table">
          <thead>
            <tr>
              <th>Parcelle</th>
              <th>Vendeur</th>
              <th>Région</th>
              <th>Surface</th>
              <th>Prix</th>
              <th>Soumis le</th>
              <th>Hash document</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of pending()"
                [class.table__row--selected]="selectedId() === p.id">
              <td>
                <div class="cell-main">{{ p.titre }}</div>
                <div class="cell-sub">{{ p.localisation }}</div>
              </td>
              <td>{{ p.vendeur_nom ?? '—' }}</td>
              <td><span class="region-tag">{{ p.region }}</span></td>
              <td>{{ p.superficie }} m²</td>
              <td class="price">{{ formatPrix(p.prix) }}</td>
              <td class="date">{{ formatDate(p.created_at) }}</td>
              <td>
                <code class="hash" *ngIf="p.document_hash">
                  {{ p.document_hash | slice:0:12 }}...
                </code>
                <span class="no-doc" *ngIf="!p.document_hash">—</span>
              </td>
              <td>
                <div class="actions">
                  <button class="btn btn--sm btn--outline"
                    (click)="openDetail(p)"><span class="material-icons" style="font-size:16px;vertical-align:middle">visibility</span></button>
                  <button class="btn btn--sm btn--success"
                    [disabled]="processingId() === p.id"
                    (click)="validate(p.id)">
                    <span *ngIf="processingId() === p.id">...</span>
                    <span *ngIf="processingId() !== p.id"><span class="material-icons" style="font-size:14px;vertical-align:middle">check_circle</span> Valider</span>
                  </button>
                  <button class="btn btn--sm btn--danger"
                    [disabled]="processingId() === p.id"
                    (click)="openRejectModal(p)">
                    <span class="material-icons" style="font-size:14px;vertical-align:middle">close</span> Rejeter
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ─── Modal détail ─── -->
      <div class="modal-overlay" *ngIf="detailParcel()" (click)="closeDetail()">
        <div class="modal" (click)="$event.stopPropagation()">
          <div class="modal__header">
            <h3>{{ detailParcel()?.titre }}</h3>
            <button class="modal__close" (click)="closeDetail()">×</button>
          </div>
          <div class="modal__body">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Région</span>
                <span class="detail-value">{{ detailParcel()?.region }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Surface</span>
                <span class="detail-value">{{ detailParcel()?.superficie }} m²</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Prix</span>
                <span class="detail-value price">{{ formatPrix(detailParcel()?.prix ?? 0) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Type</span>
                <span class="detail-value">{{ detailParcel()?.type_terrain }}</span>
              </div>
            </div>
            <div class="detail-hash" *ngIf="detailParcel()?.document_hash">
              <span class="detail-label">Hash document SHA-256</span>
              <code class="hash-full">{{ detailParcel()?.document_hash }}</code>
            </div>
          </div>
          <div class="modal__footer">
            <button class="btn btn--danger" (click)="openRejectModal(detailParcel()!); closeDetail()">
              <span class="material-icons" style="font-size:14px;vertical-align:middle">close</span> Rejeter
            </button>
            <button class="btn btn--success" (click)="validate(detailParcel()!.id); closeDetail()">
              <span class="material-icons" style="font-size:14px;vertical-align:middle">check_circle</span> Valider & Certifier
            </button>
          </div>
        </div>
      </div>

      <!-- ─── Modal rejet ─── -->
      <div class="modal-overlay" *ngIf="rejectParcel()" (click)="closeRejectModal()">
        <div class="modal modal--sm" (click)="$event.stopPropagation()">
          <div class="modal__header">
            <h3>Rejeter la parcelle</h3>
            <button class="modal__close" (click)="closeRejectModal()">×</button>
          </div>
          <div class="modal__body">
            <p class="modal__text">
              Motif du rejet pour <strong>{{ rejectParcel()?.titre }}</strong> :
            </p>
            <textarea
              [(ngModel)]="rejectReason"
              class="modal__textarea"
              rows="4"
              placeholder="Ex: Documents manquants, coordonnées GPS incorrectes..."
            ></textarea>
          </div>
          <div class="modal__footer">
            <button class="btn btn--outline" (click)="closeRejectModal()">Annuler</button>
            <button class="btn btn--danger" (click)="confirmReject()">Confirmer le rejet</button>
          </div>
        </div>
      </div>

      <!-- ─── Toast ─── -->
      <div class="toast" [class.toast--visible]="toast()">
        {{ toast() }}
      </div>
    </div>
  `,
  styles: [`
    .page-header { display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }
    .page-title  { margin: 0; font-size: 22px; font-weight: 800; color: var(--slate-900); }
    .page-header__badge {
      background: var(--amber-600); color: var(--white);
      padding: 4px 12px; border-radius: 20px;
      font-size: 13px; font-weight: 700;
    }

    .loading { display: flex; align-items: center; gap: 12px; padding: 40px;
      justify-content: center; color: var(--slate-500); }
    .spinner {
      width: 24px; height: 24px;
      border: 2px solid var(--slate-200); border-top-color: var(--green-600);
      border-radius: 50%; animation: spin .7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .empty-state {
      text-align: center; padding: 60px 24px;
      background: var(--white); border-radius: 16px;
    }
    .empty-state__icon { font-size: 56px; display: block; margin-bottom: 16px; }
    .empty-state h3 { font-size: 18px; color: var(--slate-900); margin: 0 0 8px; }
    .empty-state p  { color: var(--slate-500); margin: 0; }

    .table-card {
      background: var(--white); border-radius: 16px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
      overflow: auto;
    }
    .table { width: 100%; border-collapse: collapse; min-width: 900px; }
    .table thead tr { background: var(--slate-50); }
    .table th {
      padding: 12px 16px; text-align: left;
      font-size: 11px; font-weight: 700; color: var(--slate-500);
      text-transform: uppercase; letter-spacing: .5px;
      white-space: nowrap;
    }
    .table td {
      padding: 14px 16px; border-bottom: 1px solid var(--slate-50);
      font-size: 13px; vertical-align: middle;
    }
    .table__row--selected td { background: var(--green-50); }
    .table tbody tr:hover td  { background: var(--slate-50); }

    .cell-main  { font-weight: 600; color: var(--slate-900); }
    .cell-sub   { font-size: 11px; color: var(--slate-500); margin-top: 2px; }
    .region-tag {
      background: var(--blue-50); color: var(--blue-600);
      padding: 3px 10px; border-radius: 20px;
      font-size: 11px; font-weight: 600;
    }
    .price { font-weight: 700; color: var(--green-800); }
    .date  { color: var(--slate-500); }
    .hash  {
      font-family: monospace; font-size: 11px;
      background: var(--slate-100); padding: 2px 6px; border-radius: 4px; color: var(--blue-600);
    }
    .hash-full {
      display: block; font-family: monospace; font-size: 11px;
      background: var(--slate-100); padding: 10px; border-radius: 8px;
      color: var(--blue-600); word-break: break-all; margin-top: 6px;
    }
    .no-doc { color: var(--slate-300); }

    .actions  { display: flex; gap: 6px; align-items: center; }
    .btn { padding: 10px 18px; border-radius: 10px; border: none;
      font-size: 14px; font-weight: 600; cursor: pointer; transition: .15s; }
    .btn:disabled { opacity: .5; cursor: not-allowed; }
    .btn--sm      { padding: 6px 12px; font-size: 12px; }
    .btn--success { background: var(--green-600); color: var(--white); }
    .btn--success:hover:not(:disabled) { background: var(--green-800); }
    .btn--danger  { background: var(--red-600); color: var(--white); }
    .btn--danger:hover:not(:disabled)  { background: var(--red-700); }
    .btn--outline { background: transparent; border: 1.5px solid var(--slate-200); color: var(--slate-500); }
    .btn--outline:hover { border-color: var(--green-600); color: var(--green-600); }

    /* Modal */
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,.5);
      display: flex; align-items: center; justify-content: center;
      z-index: 1000; padding: 20px;
    }
    .modal {
      background: var(--white); border-radius: 20px;
      width: 100%; max-width: 520px;
      box-shadow: 0 24px 80px rgba(0,0,0,.25);
    }
    .modal--sm { max-width: 420px; }
    .modal__header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 20px 24px; border-bottom: 1px solid var(--slate-100);
    }
    .modal__header h3 { margin: 0; font-size: 16px; color: var(--slate-900); }
    .modal__close {
      background: none; border: none; font-size: 22px;
      cursor: pointer; color: var(--slate-500); line-height: 1;
    }
    .modal__body    { padding: 20px 24px; }
    .modal__footer  {
      display: flex; justify-content: flex-end; gap: 10px;
      padding: 16px 24px; border-top: 1px solid var(--slate-100);
    }
    .modal__text    { font-size: 14px; color: var(--slate-700); margin: 0 0 12px; }
    .modal__textarea {
      width: 100%; padding: 10px 14px;
      border: 1.5px solid var(--slate-200); border-radius: 10px;
      font-size: 13px; resize: vertical; outline: none;
      font-family: inherit; box-sizing: border-box;
    }
    .modal__textarea:focus { border-color: var(--green-600); }

    .detail-grid {
      display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
      margin-bottom: 16px;
    }
    .detail-item  { display: flex; flex-direction: column; gap: 3px; }
    .detail-label { font-size: 11px; color: var(--slate-500); font-weight: 600;
      text-transform: uppercase; letter-spacing: .5px; }
    .detail-value { font-size: 14px; color: var(--slate-900); font-weight: 500; }
    .detail-hash  { display: flex; flex-direction: column; }

    /* Toast */
    .toast {
      position: fixed; bottom: 24px; right: 24px;
      background: var(--green-600); color: var(--white);
      padding: 12px 20px; border-radius: 12px;
      font-size: 14px; font-weight: 600;
      box-shadow: 0 8px 24px rgba(22,163,74,.35);
      transform: translateY(80px); opacity: 0;
      transition: all .3s ease; pointer-events: none;
    }
    .toast--visible { transform: translateY(0); opacity: 1; }
  `],
})
export class ValidationComponent implements OnInit {
  readonly parcelsService = inject(ParcelsService);

  pending      = signal<Parcel[]>([]);
  selectedId   = signal<string | null>(null);
  processingId = signal<string | null>(null);
  detailParcel = signal<Parcel | null>(null);
  rejectParcel = signal<Parcel | null>(null);
  rejectReason = '';
  toast        = signal<string | null>(null);

  ngOnInit(): void {
    this.parcelsService.fetchPending().subscribe(r => this.pending.set(r.results));
  }

  validate(id: string): void {
    this.processingId.set(id);
    this.parcelsService.validate(id, { decision: 'approve' }).subscribe({
      next: res => {
        this.pending.update(ps => ps.filter(p => p.id !== id));
        this.processingId.set(null);
        this.showToast(`Parcelle validée ! Certification blockchain en cours…`);
      },
      error: () => this.processingId.set(null),
    });
  }

  openDetail(p: Parcel): void     { this.detailParcel.set(p); }
  closeDetail(): void             { this.detailParcel.set(null); }
  openRejectModal(p: Parcel): void { this.rejectParcel.set(p); this.rejectReason = ''; }
  closeRejectModal(): void        { this.rejectParcel.set(null); }

  confirmReject(): void {
    const p = this.rejectParcel();
    if (!p) return;
    this.parcelsService.reject(p.id, this.rejectReason).subscribe({
      next: () => {
        this.pending.update(ps => ps.filter(x => x.id !== p.id));
        this.closeRejectModal();
        this.showToast('Parcelle rejetée.');
      },
    });
  }

  private showToast(msg: string): void {
    this.toast.set(msg);
    setTimeout(() => this.toast.set(null), 3500);
  }

  formatPrix(prix: number): string {
    if (prix >= 1_000_000) return `${(prix / 1_000_000).toFixed(0)}M FCFA`;
    return `${prix.toLocaleString()} FCFA`;
  }
  formatDate(d: string): string {
    return new Date(d).toLocaleDateString('fr-SN', { day: '2-digit', month: 'short', year: 'numeric' });
  }
}


// ═══════════════════════════════════════════════════════════════