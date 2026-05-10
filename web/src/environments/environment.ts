// ═══════════════════════════════════════════════════════════════
// src/environments/environment.ts  (développement)
// ═══════════════════════════════════════════════════════════════

export const environment = {
  production:  false,
  apiUrl:      '/api',
  polygonExplorer: 'https://mumbai.polygonscan.com/tx',
};


// ═══════════════════════════════════════════════════════════════
// src/environments/environment.production.ts
// ═══════════════════════════════════════════════════════════════

export const environmentProd = {
  production:  true,
  apiUrl:      'https://api.sen-parcelle.sn/api',
  polygonExplorer: 'https://polygonscan.com/tx',
};


// ═══════════════════════════════════════════════════════════════
// proxy.conf.json  — Proxy dev (évite CORS en local)
// ═══════════════════════════════════════════════════════════════

/*
{
  "/api": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true,
    "logLevel": "debug"
  }
}
*/


// ═══════════════════════════════════════════════════════════════
// tsconfig.json
// ═══════════════════════════════════════════════════════════════

/*
{
  "compileOnSave": false,
  "compilerOptions": {
    "outDir": "./dist/out-tsc",
    "strict": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "experimentalDecorators": true,
    "moduleResolution": "bundler",
    "importHelpers": true,
    "target": "ES2022",
    "module": "ES2022",
    "lib": ["ES2022", "dom"],
    "paths": {
      "@core/*":    ["./src/app/core/*"],
      "@features/*":["./src/app/features/*"],
      "@shared/*":  ["./src/app/shared/*"],
      "@env/*":     ["./src/environments/*"]
    }
  },
  "angularCompilerOptions": {
    "enableI18nLegacyMessageIdFormat": false,
    "strictInjectionParameters": true,
    "strictInputAccessModifiers": true,
    "strictTemplates": true
  }
}
*/
