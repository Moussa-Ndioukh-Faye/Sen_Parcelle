export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@e2e.sn';
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'Admin#E2e2026';

/** Session admin enregistrée par global-setup.ts. */
export const ADMIN_STATE = 'playwright/.auth/admin.json';
