// src/app/shared/components/layout/layout.component.ts
// Shell principal de l'admin (Sidebar + Header + Content)
// ═══════════════════════════════════════════════════════════════

import {
  Component, inject, signal, computed, ChangeDetectionStrategy
} from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '@core/services/auth.service';

interface NavItem {
  path:   string;
  icon:   string;
  label:  string;
  badge?: number;
  adminOnly?: boolean;
}

@Component({
  selector:         'app-layout',
  standalone:       true,
  changeDetection:  ChangeDetectionStrategy.OnPush,
  imports:          [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  template: `
    <div class="layout">

      <!-- ═══ SIDEBAR ═══ -->
      <aside class="sidebar" [class.collapsed]="sidebarCollapsed()">
        <div class="sidebar__logo">
          <span class="sidebar__logo-icon">🏡</span>
          <span class="sidebar__logo-text" *ngIf="!sidebarCollapsed()">
            Sen<strong>_parcelle</strong>
          </span>
        </div>

        <nav class="sidebar__nav">
          <div class="sidebar__group">
            <span class="sidebar__group-label" *ngIf="!sidebarCollapsed()">
              PRINCIPAL
            </span>
            <ng-container *ngFor="let item of navItems()">
              <a
                *ngIf="!item.adminOnly || auth.isAdmin()"
                [routerLink]="item.path"
                routerLinkActive="sidebar__nav-item--active"
                class="sidebar__nav-item"
                [title]="item.label"
              >
                <span class="sidebar__nav-icon">{{ item.icon }}</span>
                <span class="sidebar__nav-label" *ngIf="!sidebarCollapsed()">
                  {{ item.label }}
                </span>
                <span class="sidebar__nav-badge" *ngIf="item.badge && item.badge > 0">
                  {{ item.badge }}
                </span>
              </a>
            </ng-container>
          </div>
        </nav>

        <div class="sidebar__footer">
          <button class="sidebar__collapse-btn" (click)="toggleSidebar()">
            {{ sidebarCollapsed() ? '→' : '←' }}
          </button>
        </div>
      </aside>

      <!-- ═══ MAIN ═══ -->
      <div class="main">

        <!-- ─── Header ─── -->
        <header class="header">
          <div class="header__left">
            <h1 class="header__title">{{ pageTitle() }}</h1>
          </div>
          <div class="header__right">
            <div class="header__search">
              <input
                type="text"
                placeholder="Rechercher..."
                class="header__search-input"
              />
            </div>
            <div class="header__notif">
              <button class="header__notif-btn">
                🔔
                <span class="header__notif-badge" *ngIf="notifCount() > 0">
                  {{ notifCount() }}
                </span>
              </button>
            </div>
            <div class="header__user" (click)="toggleUserMenu()">
              <div class="header__avatar">{{ auth.userInitials() }}</div>
              <div class="header__user-info" *ngIf="!sidebarCollapsed()">
                <span class="header__user-name">{{ auth.user()?.nom }}</span>
                <span class="header__user-role">{{ auth.user()?.role }}</span>
              </div>
            </div>
            <div class="header__user-menu" *ngIf="userMenuOpen()">
              <button class="header__menu-item" (click)="auth.logout()">
                🚪 Se déconnecter
              </button>
            </div>
          </div>
        </header>

        <!-- ─── Content ─── -->
        <main class="content">
          <router-outlet />
        </main>

      </div>
    </div>
  `,
  styles: [`
    .layout {
      display: flex;
      min-height: 100vh;
      background: #F8FAFC;
    }

    /* ── SIDEBAR ── */
    .sidebar {
      width: 240px;
      min-height: 100vh;
      background: #1E293B;
      display: flex;
      flex-direction: column;
      position: sticky;
      top: 0;
      height: 100vh;
      transition: width .2s ease;
      flex-shrink: 0;
      z-index: 100;
    }
    .sidebar.collapsed { width: 64px; }

    .sidebar__logo {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 20px 16px;
      border-bottom: 1px solid rgba(255,255,255,.08);
    }
    .sidebar__logo-icon { font-size: 24px; }
    .sidebar__logo-text {
      color: #fff;
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
    }
    .sidebar__logo-text strong { color: #4ADE80; }

    .sidebar__nav { flex: 1; padding: 12px 0; overflow-y: auto; }
    .sidebar__group { margin-bottom: 8px; }
    .sidebar__group-label {
      font-size: 10px;
      font-weight: 700;
      color: rgba(255,255,255,.35);
      letter-spacing: 1.2px;
      text-transform: uppercase;
      padding: 6px 16px;
    }

    .sidebar__nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      color: rgba(255,255,255,.55);
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      border-radius: 0;
      transition: all .15s;
      cursor: pointer;
      position: relative;
    }
    .sidebar__nav-item:hover { background: rgba(255,255,255,.06); color: #fff; }
    .sidebar__nav-item--active {
      background: rgba(74,222,128,.12);
      color: #4ADE80;
      font-weight: 600;
    }
    .sidebar__nav-item--active::before {
      content: '';
      position: absolute;
      left: 0; top: 0; bottom: 0;
      width: 3px;
      background: #4ADE80;
      border-radius: 0 2px 2px 0;
    }
    .sidebar__nav-icon { font-size: 18px; width: 22px; text-align: center; flex-shrink: 0; }
    .sidebar__nav-label { white-space: nowrap; overflow: hidden; }
    .sidebar__nav-badge {
      margin-left: auto;
      background: #DC2626;
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 20px;
      flex-shrink: 0;
    }

    .sidebar__footer {
      padding: 12px;
      border-top: 1px solid rgba(255,255,255,.08);
    }
    .sidebar__collapse-btn {
      width: 100%;
      padding: 8px;
      background: rgba(255,255,255,.06);
      border: none;
      border-radius: 8px;
      color: rgba(255,255,255,.5);
      cursor: pointer;
      font-size: 14px;
      transition: .15s;
    }
    .sidebar__collapse-btn:hover { background: rgba(255,255,255,.12); color: #fff; }

    /* ── MAIN ── */
    .main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

    /* ── HEADER ── */
    .header {
      height: 64px;
      background: #fff;
      border-bottom: 1px solid #F1F5F9;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      gap: 16px;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .header__title {
      font-size: 18px;
      font-weight: 700;
      color: #1E293B;
      margin: 0;
    }
    .header__right {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-left: auto;
    }
    .header__search-input {
      padding: 8px 14px;
      border: 1.5px solid #E2E8F0;
      border-radius: 10px;
      font-size: 13px;
      width: 200px;
      outline: none;
      transition: .15s;
    }
    .header__search-input:focus { border-color: #16A34A; }
    .header__notif-btn {
      background: none;
      border: none;
      font-size: 20px;
      cursor: pointer;
      position: relative;
      padding: 4px;
    }
    .header__notif-badge {
      position: absolute;
      top: 0; right: 0;
      background: #DC2626;
      color: #fff;
      font-size: 9px;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 10px;
    }
    .header__user {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 8px;
      transition: .15s;
    }
    .header__user:hover { background: #F8FAFC; }
    .header__avatar {
      width: 36px; height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #14532D, #16A34A);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
    }
    .header__user-name { font-size: 13px; font-weight: 600; color: #1E293B; }
    .header__user-role { font-size: 11px; color: #64748B; text-transform: capitalize; }
    .header__user-menu {
      position: absolute;
      top: 64px; right: 16px;
      background: #fff;
      border: 1px solid #E2E8F0;
      border-radius: 10px;
      padding: 6px;
      box-shadow: 0 8px 24px rgba(0,0,0,.12);
      z-index: 200;
    }
    .header__menu-item {
      display: block;
      width: 100%;
      padding: 8px 14px;
      border: none;
      background: none;
      text-align: left;
      cursor: pointer;
      font-size: 13px;
      border-radius: 6px;
      color: #DC2626;
    }
    .header__menu-item:hover { background: #FEE2E2; }

    /* ── CONTENT ── */
    .content { flex: 1; padding: 24px; overflow-y: auto; }
  `],
})
export class LayoutComponent {
  readonly auth = inject(AuthService);

  sidebarCollapsed = signal(false);
  userMenuOpen     = signal(false);
  notifCount       = signal(7);
  pageTitle        = signal('Dashboard');

  navItems = signal<NavItem[]>([
    { path: '/dashboard',    icon: '📊', label: 'Dashboard' },
    { path: '/parcelles',    icon: '🏡', label: 'Parcelles' },
    { path: '/validation',   icon: '✅', label: 'Validation', badge: 7, adminOnly: true },
    { path: '/kyc',          icon: '🪪', label: 'KYC', adminOnly: true },
    { path: '/utilisateurs', icon: '👥', label: 'Utilisateurs', adminOnly: true },
    { path: '/blockchain',   icon: '🔗', label: 'Blockchain', adminOnly: true },
  ]);

  toggleSidebar()  { this.sidebarCollapsed.update(v => !v); }
  toggleUserMenu() { this.userMenuOpen.update(v => !v); }
}