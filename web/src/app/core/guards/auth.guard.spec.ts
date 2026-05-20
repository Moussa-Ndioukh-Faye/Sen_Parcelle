import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { authGuard, adminGuard, guestGuard } from './auth.guard';

describe('AuthGuard', () => {
  let auth: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    const authSpy = jasmine.createSpyObj('AuthService', [
      'isAuthenticated', 'isAdmin',
    ]);
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });

    auth = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
  });

  describe('authGuard', () => {
    it('devrait autoriser si authentifié', () => {
      auth.isAuthenticated.and.returnValue(true);
      const guard = TestBed.runInInjectionContext(
        () => authGuard(null as any, null as any),
      );
      expect(guard).toBeTrue();
    });

    it('devrait rediriger si non authentifié', () => {
      auth.isAuthenticated.and.returnValue(false);
      const guard = TestBed.runInInjectionContext(
        () => authGuard(null as any, null as any),
      );
      expect(guard).toBeFalse();
      expect(router.navigate).toHaveBeenCalledWith(
        ['/auth/login'],
        jasmine.objectContaining({ queryParams: jasmine.any(Object) }),
      );
    });
  });

  describe('adminGuard', () => {
    it('devrait autoriser si admin', () => {
      auth.isAuthenticated.and.returnValue(true);
      auth.isAdmin.and.returnValue(true);
      const guard = TestBed.runInInjectionContext(
        () => adminGuard(null as any, null as any),
      );
      expect(guard).toBeTrue();
    });

    it('devrait refuser si non admin', () => {
      auth.isAuthenticated.and.returnValue(true);
      auth.isAdmin.and.returnValue(false);
      const guard = TestBed.runInInjectionContext(
        () => adminGuard(null as any, null as any),
      );
      expect(guard).toBeFalse();
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    });

    it('devrait rediriger si non admin', () => {
      auth.isAdmin.and.returnValue(false);
      const guard = TestBed.runInInjectionContext(
        () => adminGuard(null as any, null as any),
      );
      expect(guard).toBeFalse();
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    });
  });

  describe('guestGuard', () => {
    it('devrait autoriser si non authentifié', () => {
      auth.isAuthenticated.and.returnValue(false);
      const guard = TestBed.runInInjectionContext(
        () => guestGuard(null as any, null as any),
      );
      expect(guard).toBeTrue();
    });

    it('devrait rediriger si déjà authentifié', () => {
      auth.isAuthenticated.and.returnValue(true);
      const guard = TestBed.runInInjectionContext(
        () => guestGuard(null as any, null as any),
      );
      expect(guard).toBeFalse();
      expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    });
  });
});
