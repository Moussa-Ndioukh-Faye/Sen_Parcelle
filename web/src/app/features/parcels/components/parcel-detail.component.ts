import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { ParcelsService } from '../services/parcels.service';
import { ParcelDetail } from '@core/models';

@Component({
  selector: 'app-parcel-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="detail-container">
      @if (parcel) {
        <h2>{{ parcel.titre }}</h2>
        <p>{{ parcel.localisation }}</p>
        <p>{{ parcel.description }}</p>
        <p class="price">{{ parcel.price | currency:'XOF' }}</p>
        <p>Statut: {{ parcel.status }}</p>
      } @else {
        <p>Chargement...</p>
      }
    </div>
  `,
  styles: [`
    .detail-container { padding: 24px; max-width: 800px; margin: 0 auto; }
    .price { color: #2e7d32; font-weight: bold; font-size: 1.5em; }
  `]
})
export class ParcelDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private parcelsService = inject(ParcelsService);
  parcel?: ParcelDetail;

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.parcelsService.fetchParcelById(id).subscribe(p => this.parcel = p);
    }
  }
}
