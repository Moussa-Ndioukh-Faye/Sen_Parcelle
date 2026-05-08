// src/app/features/auth/auth.routes.ts
// ══════════════════════════════════════════════════════════════

import { Routes } from '@angular/router';

export const authRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./login.component').then(m => m.LoginComponent),
    title: 'Connexion — Sen_parcelle Admin',
  },
];
