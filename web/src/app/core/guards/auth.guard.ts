// src/app/core/guards/auth.guard.ts
// ═══════════════════════════════════════════════════════════════

import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { map } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

// Les guards attendent la restauration de session (rechargement de page)
// avant de décider, sinon un utilisateur connecté serait renvoyé vers la connexion.

export const authGuard: CanActivateFn = () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) return true;

  return auth.ensureSession().pipe(
    map(ok => {
      if (ok) return true;
      router.navigate(['/auth/login'], {
        queryParams: { returnUrl: router.url },
      });
      return false;
    }),
  );
};

export const adminGuard: CanActivateFn = () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  if (auth.isAdmin()) return true;

  return auth.ensureSession().pipe(
    map(() => {
      if (auth.isAdmin()) return true;
      router.navigate(['/dashboard']);
      return false;
    }),
  );
};

export const guestGuard: CanActivateFn = () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) {
    router.navigate(['/dashboard']);
    return false;
  }

  return auth.ensureSession().pipe(
    map(ok => {
      if (!ok) return true;
      router.navigate(['/dashboard']);
      return false;
    }),
  );
};
