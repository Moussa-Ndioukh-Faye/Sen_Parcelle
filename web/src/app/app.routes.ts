// src/app/app.routes.ts — Routes Angular avec lazy loading
// ═══════════════════════════════════════════════════════════════

import { Routes } from '@angular/router';
import { authGuard, adminGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  // ─── Auth (public) ───
  {
    path: 'auth',
    canActivate: [guestGuard],
    loadChildren: () =>
      import('./features/auth/auth.routes').then(m => m.authRoutes),
  },

  // ─── App (protégé) ───
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./shared/components/layout/layout.component').then(m => m.LayoutComponent),
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
        title: 'Dashboard — Sen_parcelle',
      },
      {
        path: 'parcelles',
        loadComponent: () =>
          import('./features/parcels/components/parcels-list.component').then(m => m.ParcelsListComponent),
        title: 'Parcelles',
      },
      {
        path: 'parcelles/:id',
        loadComponent: () =>
          import('./features/parcels/components/parcel-detail.component').then(m => m.ParcelDetailComponent),
      },
      {
        path: 'validation',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/parcels/components/validation.component').then(m => m.ValidationComponent),
        title: 'Validation — Admin',
      },
      {
        path: 'utilisateurs',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/users/components/users-list.component').then(m => m.UsersListComponent),
        title: 'Utilisateurs',
      },
      {
        path: 'kyc',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/users/components/kyc-manager.component').then(m => m.KYCManagerComponent),
        title: 'Gestion KYC',
      },
      {
        path: 'blockchain',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/blockchain/components/blockchain.component').then(m => m.BlockchainComponent),
        title: 'Blockchain',
      },
    ],
  },

  { path: '**', redirectTo: 'dashboard' },
  ];



// ═══════════════════════════════════════════════════════════════