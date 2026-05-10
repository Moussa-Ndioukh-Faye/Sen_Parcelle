// src/app/features/blockchain/components/blockchain.component.ts
// ═══════════════════════════════════════════════════════════════

import {
  Component, inject, OnInit, signal, ChangeDetectionStrategy
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ParcelsService } from '../../parcels/services/parcels.service';

@Component({
  selector:        'app-blockchain',
  standalone:      true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports:         [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h1 class="page-title">Blockchain Polygon</h1>
        <div class="page-header__network">
          <span class="network-dot"></span> Polygon Mainnet
        </div>
      </div>

      <!-- ─── Stats blockchain ─── -->
      <div class="bc-stats">
        <div class="bc-stat">
          <div class="bc-stat__icon material-icons">link</div>
          <div class="bc-stat__value">{{ certifiedCount() }}</div>
          <div class="bc-stat__label">Certificats émis</div>
        </div>
        <div class="bc-stat">
          <div class="bc-stat__icon material-icons">local_gas_station</div>
          <div class="bc-stat__value">~0.01 MATIC</div>
          <div class="bc-stat__label">Coût moyen / TX</div>
        </div>
        <div class="bc-stat">
          <div class="bc-stat__icon material-icons">bolt</div>
          <div class="bc-stat__value">~3s</div>
          <div class="bc-stat__label">Temps confirmation</div>
        </div>
        <div class="bc-stat">
          <div class="bc-stat__icon material-icons">shield</div>
          <div class="bc-stat__value">SHA-256</div>
          <div class="bc-stat__label">Algorithme de hash</div>
        </div>
      </div>

      <!-- ─── Vérificateur de certificat ─── -->
      <div class="verifier-card">
        <h2 class="verifier-card__title"><span class="material-icons" style="font-size:18px;vertical-align:middle">search</span> Vérifier un certificat</h2>
        <p class="verifier-card__sub">
          Entrez le hash SHA-256 d'un document pour vérifier son authenticité sur Polygon.
        </p>
        <div class="verifier-card__form">
          <input
            [(ngModel)]="verifyHash"
            class="verifier-card__input"
            placeholder="0x7f4e2b91a3c8d05f6e14b29a7c3d8e4f..."
          />
          <button class="btn btn--primary" (click)="verifyCert()">
            Vérifier
          </button>
        </div>
        <div class="verifier-result verifier-result--valid"
          *ngIf="verifyResult() && verifyResult()!.valide">
          <span class="material-icons" style="font-size:24px">check_circle</span>
          <div>
            <strong>Certificat valide</strong>
            <p>Parcelle : {{ verifyResult()!.parcelle }}</p>
            <p>Date validation : {{ verifyResult()!.date_validation | date:'dd/MM/yyyy' }}</p>
          </div>
        </div>
        <div class="verifier-result verifier-result--invalid"
          *ngIf="verifyResult() && !verifyResult()!.valide">
          <span class="material-icons" style="font-size:24px">cancel</span>
          <div><strong>Certificat introuvable</strong><p>Ce hash n'est pas enregistré.</p></div>
        </div>
      </div>

      <!-- ─── Parcelles certifiées ─── -->
      <div class="table-card">
        <div class="table-card__header">
          <h2>Parcelles certifiées sur blockchain</h2>
        </div>
        <table class="table">
          <thead>
            <tr>
              <th>Parcelle</th><th>Région</th><th>Hash blockchain</th>
              <th>Certifiée le</th><th>Explorer</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of certified()">
              <td>
                <div class="cell-main">{{ p.titre }}</div>
                <div class="cell-sub">{{ p.localisation }}</div>
              </td>
              <td>{{ p.region }}</td>
              <td>
                <code class="hash">
                  {{ p.blockchain_tx_hash ? (p.blockchain_tx_hash | slice:0:16) + '...' : '—' }}
                </code>
              </td>
              <td class="date">{{ p.certified_at ? formatDate(p.certified_at) : '—' }}</td>
              <td>
                <a [href]="getExplorerUrl(p.blockchain_tx_hash)"
                  target="_blank" class="explorer-link"
                  *ngIf="p.blockchain_tx_hash">
                  <span class="material-icons" style="font-size:12px;vertical-align:middle">link</span> Voir
                </a>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="empty-state" *ngIf="!certified().length">
          Aucune parcelle certifiée
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
    .page-title  { margin: 0; font-size: 22px; font-weight: 800; color: #1E293B; }
    .page-header__network {
      display: flex; align-items: center; gap: 8px;
      background: #F0FDF4; color: #16A34A;
      padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;
    }
    .network-dot {
      width: 8px; height: 8px; border-radius: 50%; background: #16A34A;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%,100% { opacity: 1; } 50% { opacity: .4; }
    }

    .bc-stats {
      display: grid; grid-template-columns: repeat(4,1fr);
      gap: 16px; margin-bottom: 24px;
    }
    @media (max-width: 900px) { .bc-stats { grid-template-columns: repeat(2,1fr); } }
    .bc-stat {
      background: #fff; border-radius: 14px; padding: 18px;
      text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,.05);
    }
    .bc-stat__icon  { font-size: 28px; margin-bottom: 8px; }
    .bc-stat__value {
      font-size: 22px; font-weight: 900; color: #1E293B;
      font-family: monospace; margin-bottom: 4px;
    }
    .bc-stat__label { font-size: 12px; color: #64748B; font-weight: 600; }

    .verifier-card {
      background: #fff; border-radius: 16px; padding: 24px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06); margin-bottom: 24px;
    }
    .verifier-card__title { font-size: 17px; font-weight: 700; color: #1E293B; margin: 0 0 6px; }
    .verifier-card__sub   { font-size: 13px; color: #64748B; margin: 0 0 18px; }
    .verifier-card__form  { display: flex; gap: 10px; }
    .verifier-card__input {
      flex: 1; padding: 12px 16px; border: 1.5px solid #E2E8F0;
      border-radius: 12px; font-size: 13px; font-family: monospace;
      outline: none;
    }
    .verifier-card__input:focus { border-color: #16A34A; }

    .verifier-result {
      display: flex; align-items: flex-start; gap: 12px;
      padding: 14px; border-radius: 12px; margin-top: 14px;
      font-size: 14px;
    }
    .verifier-result span { font-size: 24px; }
    .verifier-result p    { margin: 4px 0 0; font-size: 12px; color: #64748B; }
    .verifier-result--valid   { background: #F0FDF4; border: 1px solid #BBF7D0; }
    .verifier-result--invalid { background: #FEF2F2; border: 1px solid #FECACA; }

    .table-card {
      background: #fff; border-radius: 16px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06); overflow: auto;
    }
    .table-card__header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 20px; border-bottom: 1px solid #F1F5F9;
    }
    .table-card__header h2 { margin: 0; font-size: 15px; font-weight: 700; }
    .table { width: 100%; border-collapse: collapse; min-width: 700px; }
    .table th {
      padding: 12px 16px; text-align: left;
      font-size: 11px; font-weight: 700; color: #64748B;
      text-transform: uppercase; letter-spacing: .5px;
      background: #F8FAFC;
    }
    .table td { padding: 14px 16px; border-bottom: 1px solid #F8FAFC; font-size: 13px; }
    .cell-main { font-weight: 600; color: #1E293B; }
    .cell-sub  { font-size: 11px; color: #64748B; }
    .hash { font-family: monospace; font-size: 11px; background: #F1F5F9;
      padding: 3px 8px; border-radius: 4px; color: #2563EB; }
    .date { color: #64748B; font-size: 12px; }
    .explorer-link { color: #16A34A; font-weight: 600; text-decoration: none; font-size: 12px; }
    .explorer-link:hover { text-decoration: underline; }
    .empty-state { text-align: center; padding: 32px; color: #94A3B8; font-size: 13px; }

    .btn { padding: 10px 20px; border-radius: 10px; border: none;
      font-size: 14px; font-weight: 600; cursor: pointer; transition: .15s; }
    .btn--primary { background: #16A34A; color: #fff; }
    .btn--primary:hover { background: #14532D; }
  `],
})
export class BlockchainComponent implements OnInit {
  private readonly parcelsService = inject(ParcelsService);

  certified     = signal<any[]>([]);
  certifiedCount = signal(0);
  verifyHash    = '';
  verifyResult  = signal<any>(null);

  ngOnInit(): void {
    this.parcelsService.fetchParcels({ status: 'certified', page_size: 50 }).subscribe(r => {
      this.certified.set(r.results);
      this.certifiedCount.set(r.count);
    });
  }

  verifyCert(): void {
    if (!this.verifyHash.trim()) return;
    this.parcelsService.verifyCertificate(this.verifyHash.trim()).subscribe({
      next: result  => this.verifyResult.set(result),
      error: ()     => this.verifyResult.set({ valide: false }),
    });
  }

  getExplorerUrl(hash?: string): string {
    if (!hash) return '#';
    return `https://polygonscan.com/tx/${hash}`;
  }

  formatDate(d: string): string {
    return new Date(d).toLocaleDateString('fr-SN', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  }
}