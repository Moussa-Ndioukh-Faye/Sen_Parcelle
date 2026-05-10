// src/app/core/interceptors/jwt.interceptor.ts
// ═══════════════════════════════════════════════════════════════

import {
  HttpInterceptorFn, HttpRequest, HttpHandlerFn,
  HttpEvent, HttpErrorResponse
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, switchMap, filter, take } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

let isRefreshing = false;
const refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const jwtInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
): Observable<HttpEvent<unknown>> => {

  const auth   = inject(AuthService);
  const token  = auth.getAccessToken();

  // Routes publiques → pas d'injection de token
  const publicUrls = ['/auth/login/', '/auth/inscription/', '/auth/token/refresh/'];
  if (publicUrls.some(url => req.url.includes(url))) {
    return next(req);
  }

  const authReq = token ? addToken(req, token) : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.includes('/auth/refresh/')) {
        return handle401Error(req, next, auth);
      }
      return throwError(() => error);
    }),
  );
};

function addToken(req: HttpRequest<unknown>, token: string): HttpRequest<unknown> {
  return req.clone({
    setHeaders: { Authorization: `Bearer ${token}` },
  });
}

function handle401Error(
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
  auth: AuthService,
): Observable<HttpEvent<unknown>> {
  if (!isRefreshing) {
    isRefreshing = true;
    refreshTokenSubject.next(null);

    return auth.refreshToken().pipe(
      switchMap(({ access }) => {
        isRefreshing = false;
        refreshTokenSubject.next(access);
        return next(addToken(req, access));
      }),
      catchError(err => {
        isRefreshing = false;
        auth.logout();
        return throwError(() => err);
      }),
    );
  }

  // Attendre que le refresh soit terminé
  return refreshTokenSubject.pipe(
    filter(token => token !== null),
    take(1),
    switchMap(token => next(addToken(req, token!))),
  );
}


// ═══════════════════════════════════════════════════════════════