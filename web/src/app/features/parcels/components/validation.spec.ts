// ═══════════════════════════════════════════════════════════════
// src/app/features/auth/auth.service.spec.ts — Tests Auth
// ═══════════════════════════════════════════════════════════════

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter }  from '@angular/router';
import { AuthService }    from '@core/services/auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports:   [HttpClientTestingModule],
      providers: [AuthService, provideRouter([])],
    });
    service  = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    expect(service).toBeTruthy();
  });

  it('isAuthenticated doit être false au départ', () => {
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('login réussi doit stocker les tokens', (done) => {
    service.login({ email: 'admin@test.sn', password: 'password123' }).subscribe({
      next: response => {
        expect(response.access_token).toBeTruthy();
        expect(localStorage.getItem('access_token')).toBe('mock_access_token');
        done();
      },
    });

    const req = httpMock.expectOne(`${service['api'].baseUrl}/auth/login/`);
    expect(req.request.method).toBe('POST');
    req.flush({
      access_token:  'mock_access_token',
      refresh_token: 'mock_refresh_token',
      user_id:       'user-123',
      role:          'admin',
    });
  });

  it('login échoué doit setter error signal', (done) => {
    service.login({ email: 'bad@test.sn', password: 'wrongpass' }).subscribe({
      error: () => {
        expect(service.error()).toBeTruthy();
        expect(service.isAuthenticated()).toBeFalse();
        done();
      },
    });

    const req = httpMock.expectOne(`${service['api'].baseUrl}/auth/login/`);
    req.flush(
      { error: { code: 'invalid_credentials', message: 'Email ou mot de passe incorrect.' } },
      { status: 401, statusText: 'Unauthorized' },
    );
  });

  it('isAdmin doit retourner true si rôle admin', () => {
    service['_user'].set({
      id: '1', nom: 'Admin', email: 'admin@test.sn',
      role: 'admin', kyc_status: 'verified',
    });
    expect(service.isAdmin()).toBeTrue();
  });

  it('userInitials doit retourner les 2 premières lettres du nom', () => {
    service['_user'].set({
      id: '1', nom: 'Moussa Faye', email: 'm@test.sn',
      role: 'admin', kyc_status: 'verified',
    });
    expect(service.userInitials()).toBe('MF');
  });

  it('logout doit vider localStorage et réinitialiser user', () => {
    localStorage.setItem('access_token', 'tok');
    service['_user'].set({
      id: '1', nom: 'Admin', email: 'a@test.sn',
      role: 'admin', kyc_status: 'verified',
    });

    service.logout();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.user()).toBeNull();
  });

  it('isTokenExpired doit retourner true si pas de token', () => {
    localStorage.removeItem('access_token');
    expect(service.isTokenExpired()).toBeTrue();
  });
});


// ═══════════════════════════════════════════════════════════════
// src/app/features/parcels/services/parcels.service.spec.ts
// ═══════════════════════════════════════════════════════════════

import { TestBed }  from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ParcelsService } from './parcels.service';

describe('ParcelsService', () => {
  let service: ParcelsService;
  let httpMock: HttpTestingController;

  const mockParcels = {
    count: 2,
    page: 1,
    results: [
      {
        id: 'p1', titre: 'Terrain Almadies', localisation: 'Almadies', region: 'Dakar',
        superficie: 500, price: 25000000, type_terrain: 'residentiel',
        status: 'pending', owner_id: 'u1', created_at: new Date().toISOString(),
      },
      {
        id: 'p2', titre: 'Terrain Thiès', localisation: 'Thiès-Nord', region: 'Thiès',
        superficie: 2000, price: 8000000, type_terrain: 'agricole',
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
      expect(service.parcels()[0].titre).toBe('Terrain Almadies');
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
    // Préremplir le signal
    service['_parcels'].set(mockParcels.results as any);

    service.validate('p1', { decision: 'approve' }).subscribe(() => {
      const updated = service.parcels().find(p => p.id === 'p1');
      expect(updated?.status).toBe('validated');
      done();
    });

    const req = httpMock.expectOne(r => r.url.includes('/parcelles/p1/valider/'));
    req.flush({ status: 'validated', message: 'OK' });
  });

  it('pendingCount doit compter les parcelles en attente', () => {
    service['_parcels'].set(mockParcels.results as any);
    expect(service.pendingCount()).toBe(1);
  });

  it('deleteParcel doit retirer la parcelle du signal', (done) => {
    service['_parcels'].set(mockParcels.results as any);

    service.deleteParcel('p1').subscribe(() => {
      expect(service.parcels().length).toBe(1);
      expect(service.parcels().find(p => p.id === 'p1')).toBeUndefined();
      done();
    });

    const req = httpMock.expectOne(r => r.url.includes('/parcelles/p1/'));
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});


// ═══════════════════════════════════════════════════════════════
// src/styles.scss — Styles globaux Angular
// ═══════════════════════════════════════════════════════════════

/*
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  font-family: 'DM Sans', sans-serif;
  background: #F8FAFC;
  color: #1E293B;
  line-height: 1.5;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Syne', sans-serif;
  margin: 0;
}

a { color: #16A34A; }

:root {
  --green:         #16A34A;
  --green-dark:    #14532D;
  --green-light:   #DCFCE7;
  --green-bg:      #F0FDF4;
  --slate:         #1E293B;
  --muted:         #64748B;
  --amber:         #D97706;
  --red:           #DC2626;
  --blue:          #2563EB;
  --purple:        #7C3AED;
  --bg-light:      #F8FAFC;
  --border:        #E2E8F0;
  --radius-sm:     8px;
  --radius-md:     12px;
  --radius-lg:     16px;
  --shadow-sm:     0 2px 8px rgba(0,0,0,.06);
  --shadow-md:     0 4px 16px rgba(0,0,0,.08);
  --shadow-lg:     0 8px 32px rgba(0,0,0,.12);
}

/* Scrollbar custom */
::-webkit-scrollbar        { width: 6px; height: 6px; }
::-webkit-scrollbar-track  { background: #F1F5F9; }
::-webkit-scrollbar-thumb  { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* Animation fade-in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn .2s ease; }

/* View transitions Angular 17 */
::view-transition-old(root) { animation: fadeOut .15s ease; }
::view-transition-new(root) { animation: fadeIn  .15s ease; }
@keyframes fadeOut {
  from { opacity: 1; }
  to   { opacity: 0; }
}
*/
