import { TestBed } from '@angular/core/testing';
import {
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { HttpClient } from '@angular/common/http';
import { jwtInterceptor } from './jwt.interceptor';
import { AuthService } from '../services/auth.service';
import { Observable, of, throwError } from 'rxjs';

describe('JwtInterceptor', () => {
  let authSpy: jasmine.SpyObj<AuthService>;
  let httpMock: HttpTestingController;
  let http: HttpClient;

  beforeEach(() => {
    authSpy = jasmine.createSpyObj('AuthService', [
      'getAccessToken', 'refreshToken', 'logout',
    ]);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([jwtInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authSpy },
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    http = TestBed.inject(HttpClient);
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait injecter le token dans les requêtes authentifiées', () => {
    authSpy.getAccessToken.and.returnValue('my_token');

    http.get('/api/test/').subscribe();

    const req = httpMock.expectOne('/api/test/');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my_token');
    req.flush({});
  });

  it('devrait fonctionner sans token', () => {
    authSpy.getAccessToken.and.returnValue(null);

    http.get('/api/test/').subscribe();

    const req = httpMock.expectOne('/api/test/');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });
});
