import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ParcelsService } from '../services/parcels.service';

@Component({
  selector: 'app-parcels-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="parcels-container">
      <h2>Parcelles</h2>
      @if (parcelsService.isLoading()) {
        <p>Chargement...</p>
      } @else {
        <div class="parcels-grid">
          @for (parcel of parcelsService.parcels(); track parcel.id) {
            <div class="parcel-card">
              <h3>{{ parcel.titre }}</h3>
              <p>{{ parcel.localisation }}</p>
              <p class="price">{{ parcel.price | currency:'XOF' }}</p>
            </div>
          } @empty {
            <p>Aucune parcelle trouvée.</p>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .parcels-container { padding: 24px; }
    .parcels-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
    .parcel-card { padding: 16px; border: 1px solid #e0e0e0; border-radius: 8px; }
    .price { color: #2e7d32; font-weight: bold; font-size: 1.2em; }
  `]
})
export class ParcelsListComponent implements OnInit {
  parcelsService = inject(ParcelsService);

  ngOnInit() {
    this.parcelsService.fetchParcels().subscribe();
  }
}
