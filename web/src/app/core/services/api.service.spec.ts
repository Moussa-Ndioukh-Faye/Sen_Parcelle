import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.setItem('access_token', 'test_token');
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    expect(service).toBeTruthy();
  });

  it('get doit ajouter le token dans le header', () => {
    service.get('/test/').subscribe();
    const req = httpMock.expectOne('/api/test/');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test_token');
    req.flush({});
  });

  it('post doit envoyer les données', () => {
    service.post('/test/', { name: 'test' }).subscribe();
    const req = httpMock.expectOne('/api/test/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'test' });
    req.flush({});
  });

  it('put doit envoyer les données', () => {
    service.put('/test/1/', { name: 'updated' }).subscribe();
    const req = httpMock.expectOne('/api/test/1/');
    expect(req.request.method).toBe('PUT');
    req.flush({});
  });

  it('delete doit envoyer la requête', () => {
    service.delete('/test/1/').subscribe();
    const req = httpMock.expectOne('/api/test/1/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('baseUrl doit être /api/', () => {
    expect((service as any).baseUrl).toBe('/api');
  });
});
