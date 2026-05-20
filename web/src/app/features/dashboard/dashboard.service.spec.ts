import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { DashboardService } from './dashboard.service';

describe('DashboardService', () => {
  let service: DashboardService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [DashboardService],
    });
    service = TestBed.inject(DashboardService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.setItem('access_token', 'mock_token');
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    expect(service).toBeTruthy();
  });

  it('loadDashboard doit charger les stats', (done) => {
    service.loadDashboard().subscribe((stats) => {
      expect(stats).toBeTruthy();
      expect(stats.parcels).toBeTruthy();
      expect(stats.users).toBeTruthy();
      done();
    });

    const pendingReq = httpMock.expectOne((r) =>
      r.url.includes('/parcelles/') && r.params.get('status') === 'pending'
    );
    pendingReq.flush({ count: 5 });

    const certifiedReq = httpMock.expectOne((r) =>
      r.url.includes('/parcelles/') && r.params.get('status') === 'certified'
    );
    certifiedReq.flush({ count: 10 });

    const kycReq = httpMock.expectOne((r) =>
      r.url.includes('/utilisateurs/') && r.params.get('kyc_status') === 'pending'
    );
    kycReq.flush({ count: 3 });

    const usersReq = httpMock.expectOne((r) =>
      r.url.includes('/utilisateurs/')
    );
    usersReq.flush({ count: 50 });
  });

  it('devrait avoir isLoading à false initialement', () => {
    expect(service.isLoading()).toBeFalse();
  });

  it('devrait avoir stats null initialement', () => {
    expect(service.stats()).toBeNull();
  });
});
