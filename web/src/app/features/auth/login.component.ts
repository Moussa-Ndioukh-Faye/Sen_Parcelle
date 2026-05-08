// src/app/features/auth/login.component.ts
// ═══════════════════════════════════════════════════════════════

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
      <div class="login-card">
        <!-- ─── Left panel ─── -->
        <div class="login-card__left">
          <div class="login-card__brand">
            <span class="login-card__brand-icon">🏡</span>
            <div>
              <h1 class="login-card__title">Sen_parcelle</h1>
              <p class="login-card__subtitle">Plateforme foncière sécurisée · Sénégal</p>
            </div>
          </div>
          <ul class="login-card__features">
            <li *ngFor="let f of features">
              <span>{{ f.icon }}</span> {{ f.label }}
            </li>
          </ul>
          <div class="login-card__cert">🔗 Certifié sur Blockchain Polygon</div>
        </div>

        <!-- ─── Right panel (formulaire) ─── -->
        <div class="login-card__right">
          <h2 class="login-form__title">Connexion Admin</h2>
          <p class="login-form__sub">Accès réservé aux administrateurs</p>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="login-form">

            <div class="login-form__group">
              <label class="login-form__label">Email</label>
              <input
                type="email"
                formControlName="email"
                class="login-form__input"
                [class.login-form__input--error]="isInvalid('email')"
                placeholder="admin@sen-parcelle.sn"
              />
              <span class="login-form__error" *ngIf="isInvalid('email')">
                Email invalide
              </span>
            </div>

            <div class="login-form__group">
              <label class="login-form__label">Mot de passe</label>
              <div class="login-form__input-wrap">
                <input
                  [type]="showPassword() ? 'text' : 'password'"
                  formControlName="password"
                  class="login-form__input"
                  [class.login-form__input--error]="isInvalid('password')"
                  placeholder="••••••••"
                />
                <button type="button" class="login-form__eye"
                  (click)="showPassword.update(v => !v)">
                  {{ showPassword() ? '🙈' : '👁️' }}
                </button>
              </div>
              <span class="login-form__error" *ngIf="isInvalid('password')">
                Minimum 8 caractères
              </span>
            </div>

            <!-- Erreur API -->
            <div class="login-form__alert" *ngIf="auth.error()">
              ⚠️ {{ auth.error() }}
            </div>

            <button
              type="submit"
              class="login-form__btn"
              [disabled]="form.invalid || auth.isLoading()"
            >
              <span *ngIf="!auth.isLoading()">Se connecter</span>
              <span *ngIf="auth.isLoading()">Connexion en cours...</span>
            </button>

          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-page {
      min-height: 100vh;
      background: linear-gradient(135deg, #052E16 0%, #14532D 50%, #166534 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .login-card {
      display: flex;
      width: 100%;
      max-width: 900px;
      background: #fff;
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 24px 80px rgba(0,0,0,.3);
    }

    .login-card__left {
      flex: 1;
      background: linear-gradient(145deg, #052E16, #166534);
      padding: 48px 40px;
      display: flex;
      flex-direction: column;
      gap: 32px;
      color: #fff;
    }
    .login-card__brand { display: flex; align-items: center; gap: 14px; }
    .login-card__brand-icon { font-size: 48px; }
    .login-card__title { font-size: 28px; font-weight: 900; margin: 0; }
    .login-card__subtitle { font-size: 13px; opacity: .7; margin: 4px 0 0; }

    .login-card__features {
      list-style: none;
      padding: 0; margin: 0;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .login-card__features li {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;
      opacity: .85;
    }
    .login-card__cert {
      margin-top: auto;
      font-size: 12px;
      opacity: .6;
    }

    .login-card__right {
      flex: 1;
      padding: 48px 40px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .login-form__title { font-size: 22px; font-weight: 800; color: #1E293B; margin: 0 0 6px; }
    .login-form__sub   { font-size: 14px; color: #64748B; margin: 0 0 28px; }

    .login-form { display: flex; flex-direction: column; gap: 18px; }
    .login-form__group { display: flex; flex-direction: column; gap: 6px; }
    .login-form__label { font-size: 13px; font-weight: 600; color: #374151; }
    .login-form__input-wrap { position: relative; }
    .login-form__input {
      width: 100%;
      padding: 12px 16px;
      border: 1.5px solid #E2E8F0;
      border-radius: 12px;
      font-size: 14px;
      outline: none;
      transition: .15s;
      box-sizing: border-box;
    }
    .login-form__input:focus { border-color: #16A34A; box-shadow: 0 0 0 3px rgba(22,163,74,.1); }
    .login-form__input--error { border-color: #DC2626; }
    .login-form__eye {
      position: absolute;
      right: 12px; top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      cursor: pointer;
      font-size: 16px;
    }
    .login-form__error { font-size: 12px; color: #DC2626; }
    .login-form__alert {
      background: #FEF2F2;
      border: 1px solid #FECACA;
      border-radius: 10px;
      padding: 12px 14px;
      font-size: 13px;
      color: #DC2626;
    }
    .login-form__btn {
      padding: 14px;
      background: linear-gradient(135deg, #14532D, #16A34A);
      color: #fff;
      border: none;
      border-radius: 12px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: .15s;
      margin-top: 4px;
    }
    .login-form__btn:hover:not(:disabled) { opacity: .9; transform: translateY(-1px); }
    .login-form__btn:disabled { opacity: .6; cursor: not-allowed; }

    @media (max-width: 700px) {
      .login-card { flex-direction: column; }
      .login-card__left { padding: 32px 24px; }
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
    { icon: '✅', label: 'Validation des parcelles foncières' },
    { icon: '🪪', label: 'Vérification KYC des utilisateurs' },
    { icon: '🔗', label: 'Certification blockchain Polygon' },
    { icon: '👥', label: 'Gestion complète des utilisateurs' },
    { icon: '📊', label: 'Statistiques et rapports' },
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