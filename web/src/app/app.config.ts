// ═══════════════════════════════════════════════════════════════
// src/app/app.config.ts — Bootstrap Angular 17 standalone
// ═══════════════════════════════════════════════════════════════

import { ApplicationConfig } from '@angular/core';
import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';
import {
  provideHttpClient,
  withInterceptors,
  withFetch
} from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { routes } from './app.routes';
import { jwtInterceptor } from './core/interceptors/jwt.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes,
      withComponentInputBinding(),
      withViewTransitions(),
    ),
    provideHttpClient(
      withFetch(),
      withInterceptors([jwtInterceptor]),
    ),
    provideAnimations(),
  ],
};


// ═══════════════════════════════════════════════════════════════