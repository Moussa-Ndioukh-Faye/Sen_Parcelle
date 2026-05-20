import {
  Component, inject, signal, computed, ChangeDetectionStrategy, HostListener
} from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, NavigationEnd, Router } from '@angular/router';
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

      <aside class="sidebar" [class.collapsed]="sidebarCollapsed()">

        <div class="sidebar__logo">
          <div class="sidebar__logo-icon">
            <span class="material-icons">home</span>
          </div>
          @if (!sidebarCollapsed()) {
            <span class="sidebar__logo-text">Sen<strong>_parcelle</strong></span>
          }
        </div>

        <nav class="sidebar__nav">
          <div class="sidebar__group">
            @if (!sidebarCollapsed()) {
              <span class="sidebar__group-label">PRINCIPAL</span>
            }
            @for (item of navItems(); track item.path) {
              @if (!item.adminOnly || auth.isAdmin()) {
                <a
                  [routerLink]="item.path"
                  routerLinkActive="sidebar__nav-item--active"
                  class="sidebar__nav-item"
                  [title]="sidebarCollapsed() ? item.label : ''"
                >
                  <span class="sidebar__nav-icon material-icons">{{ item.icon }}</span>
                  @if (!sidebarCollapsed()) {
                    <span class="sidebar__nav-label">{{ item.label }}</span>
                  }
                  @if (item.badge && item.badge > 0) {
                    <span class="sidebar__nav-badge">{{ item.badge }}</span>
                  }
                </a>
              }
            }
          </div>
        </nav>

        <div class="sidebar__footer">
          <button class="sidebar__collapse-btn" (click)="toggleSidebar()" [title]="sidebarCollapsed() ? 'Ouvrir' : 'Réduire'">
            <span class="material-icons" [class.rotated]="sidebarCollapsed()">chevron_left</span>
          </button>
        </div>

      </aside>

      <div class="main">

        <header class="header">
          <div class="header__left">
            <button class="header__mobile-menu" (click)="mobileSidebar.set(!mobileSidebar())">
              <span class="material-icons">menu</span>
            </button>
            <h1 class="header__title">{{ pageTitle() }}</h1>
          </div>
          <div class="header__right">
            <div class="header__search">
              <span class="header__search-icon material-icons">search</span>
              <input
                type="text"
                placeholder="Rechercher..."
                class="header__search-input"
              />
            </div>
            <button class="header__notif-btn">
              <span class="material-icons">notifications</span>
              @if (notifCount() > 0) {
                <span class="header__notif-badge">{{ notifCount() }}</span>
              }
            </button>
            <div class="header__user" (click)="toggleUserMenu()" (clickOutside)="userMenuOpen.set(false)">
              <div class="header__avatar">{{ auth.userInitials() }}</div>
              <div class="header__user-info">
                <span class="header__user-name">{{ auth.user()?.nom }}</span>
                <span class="header__user-role">{{ auth.user()?.role }}</span>
              </div>
              <span class="header__user-chevron material-icons">expand_more</span>
            </div>
          </div>
          @if (userMenuOpen()) {
            <div class="header__user-menu scale-in">
              <div class="header__menu-user">
                <div class="header__menu-avatar">{{ auth.userInitials() }}</div>
                <div>
                  <div class="header__menu-name">{{ auth.user()?.nom }}</div>
                  <div class="header__menu-email">{{ auth.user()?.email }}</div>
                </div>
              </div>
              <div class="header__menu-divider"></div>
              <button class="header__menu-item header__menu-item--danger" (click)="auth.logout()">
                <span class="material-icons">exit_to_app</span> Se déconnecter
              </button>
            </div>
          }
        </header>

        <main class="content">
          <router-outlet />
        </main>

      </div>

      @if (mobileSidebar()) {
        <div class="mobile-overlay" (click)="mobileSidebar.set(false)"></div>
      }
    </div>
  `,
  styles: [`
    .layout {
      display: flex;
      min-height: 100vh;
      background: var(--slate-50);
    }

    .sidebar {
      width: 260px;
      min-height: 100vh;
      background: var(--slate-900);
      display: flex;
      flex-direction: column;
      position: sticky;
      top: 0;
      height: 100vh;
      transition: width 0.25s var(--ease-out);
      flex-shrink: 0;
      z-index: 100;
      overflow: hidden;
    }
    .sidebar.collapsed { width: 68px; }

    .sidebar__logo {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 22px 18px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .sidebar__logo-icon {
      width: 34px; height: 34px;
      background: rgba(74,222,128,0.12);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: var(--green-400);
      flex-shrink: 0;
    }
    .sidebar__logo-text {
      color: var(--white);
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
    }
    .sidebar__logo-text strong { color: var(--green-400); }

    .sidebar__nav { flex: 1; padding: 12px 0; overflow-y: auto; overflow-x: hidden; }
    .sidebar__nav::-webkit-scrollbar { width: 3px; }
    .sidebar__nav::-webkit-scrollbar-track { background: transparent; }
    .sidebar__nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

    .sidebar__group { margin-bottom: 8px; }
    .sidebar__group-label {
      display: block;
      font-size: 10px;
      font-weight: 700;
      color: rgba(255,255,255,0.3);
      letter-spacing: 1.2px;
      text-transform: uppercase;
      padding: 8px 18px 6px;
    }

    .sidebar__nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 18px;
      color: rgba(255,255,255,0.5);
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.15s var(--ease-out);
      cursor: pointer;
      position: relative;
      margin: 1px 8px;
      border-radius: var(--radius-md);
    }
    .sidebar__nav-item:hover {
      background: rgba(255,255,255,0.06);
      color: var(--white);
    }
    .sidebar__nav-item--active {
      background: rgba(74,222,128,0.1);
      color: var(--green-400);
      font-weight: 600;
    }
    .sidebar__nav-item--active::before {
      content: '';
      position: absolute;
      left: -8px; top: 6px; bottom: 6px;
      width: 3px;
      background: var(--green-400);
      border-radius: 0 3px 3px 0;
    }
    .sidebar__nav-icon {
      font-size: 20px;
      width: 22px;
      text-align: center;
      flex-shrink: 0;
    }
    .sidebar__nav-label { white-space: nowrap; overflow: hidden; }
    .sidebar__nav-badge {
      margin-left: auto;
      background: var(--red-500);
      color: var(--white);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 20px;
      flex-shrink: 0;
      min-width: 20px;
      text-align: center;
    }

    .sidebar__footer {
      padding: 12px;
      border-top: 1px solid rgba(255,255,255,0.06);
    }
    .sidebar__collapse-btn {
      width: 100%;
      padding: 8px;
      background: rgba(255,255,255,0.04);
      border: none;
      border-radius: var(--radius-md);
      color: rgba(255,255,255,0.35);
      cursor: pointer;
      font-size: 14px;
      transition: all 0.15s var(--ease-out);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .sidebar__collapse-btn:hover {
      background: rgba(255,255,255,0.08);
      color: var(--white);
    }
    .sidebar__collapse-btn .material-icons {
      transition: transform 0.25s var(--ease-out);
    }
    .sidebar__collapse-btn .material-icons.rotated {
      transform: rotate(180deg);
    }

    .main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

    .header {
      height: 68px;
      background: rgba(255,255,255,0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--slate-100);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      gap: 16px;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .header__left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .header__mobile-menu {
      display: none;
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: var(--slate-600);
      padding: 4px;
    }
    .header__title {
      font-size: 18px;
      font-weight: 700;
      color: var(--slate-900);
      margin: 0;
      letter-spacing: -0.3px;
    }
    .header__right {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-left: auto;
    }
    .header__search {
      position: relative;
      display: flex;
      align-items: center;
    }
    .header__search-icon {
      position: absolute;
      left: 12px;
      font-size: 18px;
      color: var(--slate-400);
      pointer-events: none;
    }
    .header__search-input {
      padding: 8px 12px 8px 38px;
      border: 1.5px solid var(--slate-200);
      border-radius: var(--radius-md);
      font-size: 13px;
      width: 220px;
      outline: none;
      transition: all 0.15s var(--ease-out);
      background: var(--slate-50);
    }
    .header__search-input:focus {
      border-color: var(--green-400);
      box-shadow: 0 0 0 3px rgba(22,163,74,0.08);
      background: var(--white);
      width: 280px;
    }
    .header__notif-btn {
      background: none;
      border: none;
      font-size: 22px;
      cursor: pointer;
      position: relative;
      padding: 6px;
      border-radius: var(--radius-md);
      color: var(--slate-500);
      transition: all 0.15s;
      display: flex;
    }
    .header__notif-btn:hover { background: var(--slate-100); color: var(--slate-700); }
    .header__notif-badge {
      position: absolute;
      top: 3px; right: 3px;
      background: var(--red-500);
      color: var(--white);
      font-size: 9px;
      font-weight: 700;
      padding: 1px 5px;
      border-radius: 10px;
      min-width: 16px;
      text-align: center;
    }

    .header__user {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      padding: 5px 10px 5px 5px;
      border-radius: var(--radius-md);
      transition: all 0.15s;
      position: relative;
    }
    .header__user:hover { background: var(--slate-100); }
    .header__avatar {
      width: 36px; height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--green-800), var(--green-500));
      color: var(--white);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 13px;
      flex-shrink: 0;
    }
    .header__user-info { line-height: 1.3; }
    .header__user-name { display: block; font-size: 13px; font-weight: 600; color: var(--slate-900); }
    .header__user-role { display: block; font-size: 11px; color: var(--slate-500); text-transform: capitalize; }
    .header__user-chevron {
      font-size: 18px;
      color: var(--slate-400);
      transition: transform 0.2s var(--ease-out);
    }
    .header__user:hover .header__user-chevron { color: var(--slate-600); }

    .header__user-menu {
      position: absolute;
      top: 60px;
      right: 28px;
      background: var(--white);
      border: 1px solid var(--slate-200);
      border-radius: var(--radius-lg);
      padding: 8px;
      min-width: 220px;
      box-shadow: var(--shadow-xl);
      z-index: 200;
    }
    .header__menu-user {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 12px;
    }
    .header__menu-avatar {
      width: 40px; height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--green-800), var(--green-500));
      color: var(--white);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 14px;
    }
    .header__menu-name { font-size: 14px; font-weight: 600; color: var(--slate-900); }
    .header__menu-email { font-size: 12px; color: var(--slate-500); }
    .header__menu-divider { height: 1px; background: var(--slate-100); margin: 6px 0; }
    .header__menu-item {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 10px 12px;
      border: none;
      background: none;
      text-align: left;
      cursor: pointer;
      font-size: 13px;
      border-radius: var(--radius-md);
      color: var(--slate-700);
      transition: all 0.15s;
      font-family: var(--font-body);
    }
    .header__menu-item:hover { background: var(--slate-50); }
    .header__menu-item--danger { color: var(--red-600); }
    .header__menu-item--danger:hover { background: var(--red-50); }

    .content { flex: 1; padding: 28px; overflow-y: auto; }

    .mobile-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.4);
      z-index: 99;
    }

    @media (max-width: 768px) {
      .sidebar { position: fixed; z-index: 100; transform: translateX(0); }
      .sidebar.collapsed { transform: translateX(-100%); width: 260px; }
      .sidebar.collapsed .sidebar__logo-text,
      .sidebar.collapsed .sidebar__nav-label,
      .sidebar.collapsed .sidebar__group-label,
      .sidebar.collapsed .sidebar__nav-badge { display: none; }
      .sidebar.collapsed .sidebar__nav-item { justify-content: center; padding: 12px; }
      .header__mobile-menu { display: flex; }
      .header__search-input { width: 140px; }
      .header__search-input:focus { width: 180px; }
      .mobile-overlay { display: block; }
      .content { padding: 20px; }
    }
  `],
})
export class LayoutComponent {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  sidebarCollapsed = signal(false);
  userMenuOpen     = signal(false);
  notifCount       = signal(7);
  mobileSidebar    = signal(false);
  pageTitle        = signal('Dashboard');

  navItems = signal<NavItem[]>([
    { path: '/dashboard',    icon: 'bar_chart', label: 'Dashboard' },
    { path: '/parcelles',    icon: 'home',       label: 'Parcelles' },
    { path: '/validation',   icon: 'check_circle', label: 'Validation', badge: 7, adminOnly: true },
    { path: '/kyc',          icon: 'badge',        label: 'KYC', adminOnly: true },
    { path: '/utilisateurs', icon: 'group',        label: 'Utilisateurs', adminOnly: true },
    { path: '/blockchain',   icon: 'link',         label: 'Blockchain', adminOnly: true },
  ]);

  constructor() {
    this.router.events.subscribe(e => {
      if (e instanceof NavigationEnd) {
        const item = this.navItems().find(n => e.urlAfterRedirects.startsWith(n.path));
        if (item) this.pageTitle.set(item.label);
        this.userMenuOpen.set(false);
        this.mobileSidebar.set(false);
      }
    });
  }

  @HostListener('document:click', ['$event'])
  onDocClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.header__user') && !target.closest('.header__user-menu')) {
      this.userMenuOpen.set(false);
    }
  }

  toggleSidebar()  { this.sidebarCollapsed.update(v => !v); }
  toggleUserMenu() { this.userMenuOpen.update(v => !v); }
}
