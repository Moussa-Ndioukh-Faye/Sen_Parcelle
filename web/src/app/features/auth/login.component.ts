import {
  Component, inject, signal, ChangeDetectionStrategy
} from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '@core/services/auth.service';

@Component({
  selector:        'app-login',
  standalone:      true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports:         [CommonModule, ReactiveFormsModule],
  template: `
    <div class="login-page">
      <div class="login-bg-pattern"></div>
      <div class="login-card">
        <div class="login-card__left">
          <div class="login-card__brand">
            <div class="login-card__brand-icon">
              <span class="material-icons">home</span>
            </div>
            <div>
              <h1 class="login-card__title">Sen_parcelle</h1>
              <p class="login-card__subtitle">Plateforme foncière sécurisée · Sénégal</p>
            </div>
          </div>

          <div class="login-card__divider"></div>

          <ul class="login-card__features">
            <li *ngFor="let f of features; let i = index" style="animation-delay: {{ i * 0.08 }}s">
              <span class="feature-icon">
                <span class="material-icons">{{ f.icon }}</span>
              </span>
              <span>{{ f.label }}</span>
            </li>
          </ul>

          <div class="login-card__footer">
            <div class="login-card__cert">
              <span class="material-icons">verified</span>
              Certifié sur Blockchain Polygon
            </div>
          </div>
        </div>

        <div class="login-card__right">
          <div class="login-form__header">
            <h2 class="login-form__title">Connexion Admin</h2>
            <p class="login-form__sub">Accès réservé aux administrateurs</p>
          </div>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="login-form">

            <div class="login-form__group">
              <label class="login-form__label">Email</label>
              <div class="login-form__input-wrap">
                <span class="login-form__input-icon material-icons">email</span>
                <input
                  type="email"
                  formControlName="email"
                  class="login-form__input"
                  [class.input--error]="isInvalid('email')"
                  placeholder="admin@sen-parcelle.sn"
                  autocomplete="email"
                />
              </div>
              <span class="login-form__error" *ngIf="isInvalid('email')">
                <span class="material-icons">error</span> Email invalide
              </span>
            </div>

            <div class="login-form__group">
              <label class="login-form__label">Mot de passe</label>
              <div class="login-form__input-wrap">
                <span class="login-form__input-icon material-icons">lock</span>
                <input
                  [type]="showPassword() ? 'text' : 'password'"
                  formControlName="password"
                  class="login-form__input"
                  [class.input--error]="isInvalid('password')"
                  placeholder="••••••••"
                  autocomplete="current-password"
                />
                <button type="button" class="login-form__eye" (click)="showPassword.set(!showPassword())">
                  <span class="material-icons">{{ showPassword() ? 'visibility_off' : 'visibility' }}</span>
                </button>
              </div>
              <span class="login-form__error" *ngIf="isInvalid('password')">
                <span class="material-icons">error</span> Minimum 8 caractères
              </span>
            </div>

            <div class="login-form__alert" *ngIf="auth.error()">
              <span class="material-icons">warning</span>
              <span>{{ auth.error() }}</span>
            </div>

            <button
              type="submit"
              class="login-form__btn"
              [disabled]="form.invalid || auth.isLoading()"
              [class.btn--loading]="auth.isLoading()"
            >
              <span *ngIf="!auth.isLoading()">Se connecter</span>
              <span *ngIf="auth.isLoading()">Connexion en cours</span>
            </button>

          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-page {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: var(--space-24);
      background: var(--slate-900);
      position: relative;
      overflow: hidden;
    }
    .login-bg-pattern {
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 80% 60% at 20% 50%, rgba(22,163,74,0.15) 0%, transparent 70%),
        radial-gradient(ellipse 60% 50% at 80% 30%, rgba(74,222,128,0.08) 0%, transparent 70%),
        radial-gradient(ellipse 50% 40% at 50% 80%, rgba(5,46,22,0.3) 0%, transparent 70%);
      pointer-events: none;
    }

    .login-card {
      display: flex;
      width: 100%;
      max-width: 920px;
      background: var(--white);
      border-radius: var(--radius-2xl);
      overflow: hidden;
      box-shadow: var(--shadow-2xl);
      animation: scaleIn 0.4s var(--ease-out);
      position: relative;
      z-index: 1;
    }

    .login-card__left {
      flex: 1;
      background: linear-gradient(160deg, var(--green-950) 0%, var(--green-900) 40%, var(--green-800) 100%);
      padding: 48px 40px;
      display: flex;
      flex-direction: column;
      gap: var(--space-32);
      color: var(--white);
      position: relative;
      overflow: hidden;
    }
    .login-card__left::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -30%;
      width: 300px; height: 300px;
      background: radial-gradient(circle, rgba(74,222,128,0.08) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }
    .login-card__brand { display: flex; align-items: center; gap: 14px; position: relative; z-index: 1; }
    .login-card__brand-icon {
      width: 52px; height: 52px;
      background: rgba(74,222,128,0.15);
      border-radius: var(--radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      color: var(--green-400);
      flex-shrink: 0;
    }
    .login-card__title { font-size: 26px; font-weight: 900; margin: 0; letter-spacing: -0.5px; }
    .login-card__subtitle { font-size: 13px; opacity: .65; margin: 4px 0 0; }

    .login-card__divider {
      width: 40px;
      height: 2px;
      background: var(--green-500);
      opacity: 0.4;
      border-radius: var(--radius-full);
    }

    .login-card__features {
      list-style: none;
      padding: 0; margin: 0;
      display: flex;
      flex-direction: column;
      gap: 16px;
      position: relative;
      z-index: 1;
    }
    .login-card__features li {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      opacity: .85;
      animation: slideInRight 0.3s var(--ease-out) both;
    }
    .feature-icon {
      width: 32px; height: 32px;
      background: rgba(74,222,128,0.1);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: var(--green-400);
      flex-shrink: 0;
    }

    .login-card__footer {
      margin-top: auto;
      position: relative;
      z-index: 1;
    }
    .login-card__cert {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      opacity: .5;
      background: rgba(255,255,255,0.05);
      padding: 6px 12px;
      border-radius: var(--radius-full);
    }
    .login-card__cert .material-icons { font-size: 14px; }

    .login-card__right {
      flex: 1;
      padding: 52px 44px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .login-form__header { margin-bottom: 32px; }
    .login-form__title { font-size: 24px; font-weight: 800; color: var(--slate-900); margin: 0 0 6px; }
    .login-form__sub   { font-size: 14px; color: var(--slate-500); margin: 0; }

    .login-form { display: flex; flex-direction: column; gap: 20px; }
    .login-form__group { display: flex; flex-direction: column; gap: 6px; }
    .login-form__label { font-size: 13px; font-weight: 600; color: var(--slate-700); }

    .login-form__input-wrap {
      position: relative;
      display: flex;
      align-items: center;
    }
    .login-form__input-icon {
      position: absolute;
      left: 14px;
      font-size: 18px;
      color: var(--slate-400);
      pointer-events: none;
      z-index: 1;
    }
    .login-form__input {
      width: 100%;
      padding: 12px 14px 12px 44px;
      border: 1.5px solid var(--slate-200);
      border-radius: var(--radius-md);
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s var(--ease-out), box-shadow 0.15s var(--ease-out);
      background: var(--slate-50);
    }
    .login-form__input:focus {
      border-color: var(--green-500);
      box-shadow: 0 0 0 3px rgba(22,163,74,0.12);
      background: var(--white);
    }
    .login-form__input.input--error {
      border-color: var(--red-500);
      background: var(--red-50);
    }
    .login-form__eye {
      position: absolute;
      right: 12px;
      background: none;
      border: none;
      cursor: pointer;
      font-size: 18px;
      color: var(--slate-400);
      padding: 4px;
      display: flex;
      transition: color .15s;
    }
    .login-form__eye:hover { color: var(--slate-600); }
    .login-form__error {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: var(--red-600);
    }
    .login-form__error .material-icons { font-size: 14px; }

    .login-form__alert {
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--red-50);
      border: 1px solid var(--red-100);
      border-radius: var(--radius-md);
      padding: var(--space-12) 14px;
      font-size: 13px;
      color: var(--red-700);
      animation: slideUp 0.2s var(--ease-out);
    }
    .login-form__alert .material-icons { font-size: 18px; color: var(--red-500); }

    .login-form__btn {
      padding: 14px 24px;
      background: linear-gradient(135deg, var(--green-800), var(--green-600));
      color: var(--white);
      border: none;
      border-radius: var(--radius-md);
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s var(--ease-out);
      margin-top: var(--space-4);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--space-8);
    }
    .login-form__btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(22,163,74,0.25);
    }
    .login-form__btn:active:not(:disabled) {
      transform: translateY(0);
    }
    .login-form__btn:disabled {
      opacity: .5;
      cursor: not-allowed;
    }

    @media (max-width: 720px) {
      .login-card { flex-direction: column; max-width: 420px; }
      .login-card__left { padding: var(--space-32) var(--space-24); }
      .login-card__right { padding: var(--space-32) var(--space-24); }
      .login-form__header { margin-bottom: 24px; }
    }
  `],
})
export class LoginComponent {
  readonly auth = inject(AuthService);

  private readonly fb     = inject(FormBuilder);
  private readonly router = inject(Router);

  showPassword = signal(false);

  form: FormGroup = this.fb.group({
    email:    ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  features = [
    { icon: 'check_circle', label: 'Validation des parcelles foncières' },
    { icon: 'badge',        label: 'Vérification KYC des utilisateurs' },
    { icon: 'link',         label: 'Certification blockchain Polygon' },
    { icon: 'group',        label: 'Gestion complète des utilisateurs' },
    { icon: 'bar_chart',    label: 'Statistiques et rapports' },
  ];

  isInvalid(field: string): boolean {
    const ctrl = this.form.get(field);
    return !!(ctrl?.invalid && ctrl?.touched);
  }

  onSubmit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.auth.login(this.form.value).subscribe({
      next: response => {
        if (!response.requires_otp) {
          this.router.navigate(['/dashboard']);
        }
      },
      error: () => {},
    });
  }
}
