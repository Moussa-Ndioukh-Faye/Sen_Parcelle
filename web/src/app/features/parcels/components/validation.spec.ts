// ═══════════════════════════════════════════════════════════════
// src/app/features/parcels/services/parcels.service.spec.ts
// ═══════════════════════════════════════════════════════════════

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ParcelsService } from '../services/parcels.service';

describe('ParcelsService', () => {
  let service: ParcelsService;
  let httpMock: HttpTestingController;

  const mockParcels = {
    count: 2,
    page: 1,
    results: [
      {
        id: 'p1', titre: 'Terrain Almadies', localisation: 'Almadies', region: 'Dakar',
        superficie: 500, prix: 25000000, type_terrain: 'residentiel',
        status: 'pending', owner_id: 'u1', created_at: new Date().toISOString(),
      },
      {
        id: 'p2', titre: 'Terrain Thiès', localisation: 'Thiès-Nord', region: 'Thiès',
        superficie: 2000, prix: 8000000, type_terrain: 'agricole',
        status: 'certified', owner_id: 'u2', created_at: new Date().toISOString(),
      },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports:   [HttpClientTestingModule],
      providers: [ParcelsService],
    });
    service  = TestBed.inject(ParcelsService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.setItem('access_token', 'mock_token');
  });

  afterEach(() => { httpMock.verify(); localStorage.clear(); });

  it('devrait être créé', () => {
    expect(service).toBeTruthy();
  });

  it('fetchParcels doit charger les parcelles dans le signal', (done) => {
    service.fetchParcels().subscribe(() => {
      expect(service.parcels().length).toBe(2);
      expect(service.total()).toBe(2);
      done();
    });

    const req = httpMock.expectOne(r => r.url.includes('/parcelles/'));
    req.flush(mockParcels);
  });

  it('fetchPending doit filtrer par statut pending', (done) => {
    service.fetchPending().subscribe(() => { done(); });

    const req = httpMock.expectOne(r =>
      r.url.includes('/parcelles/') && r.params.get('status') === 'pending'
    );
    expect(req.request.method).toBe('GET');
    req.flush({ count: 0, page: 1, results: [] });
  });

  it('validate doit mettre à jour le statut localement', (done) => {
    (service as any)['_parcels'].set(mockParcels.results as any);

    service.validate('p1', { decision: 'approve' }).subscribe(() => {
      const updated = service.parcels().find(p => p.id === 'p1');
      expect(updated?.status).toBe('validated');
      done();
    });

    const req = httpMock.expectOne(r => r.url.includes('/parcelles/p1/valider/'));
    req.flush({ status: 'validated', message: 'OK' });
  });

  it('pendingCount doit compter les parcelles en attente', () => {
    (service as any)['_parcels'].set(mockParcels.results as any);
    expect(service.pendingCount()).toBe(1);
  });

  it('deleteParcel doit retirer la parcelle du signal', (done) => {
    (service as any)['_parcels'].set(mockParcels.results as any);

    service.deleteParcel('p1').subscribe(() => {
      expect(service.parcels().length).toBe(1);
      done();
    });

    const req = httpMock.expectOne(r => r.url.includes('/parcelles/p1/'));
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
