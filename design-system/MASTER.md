# Sen_Parcelle — Master Design System

> Plateforme foncière sécurisée · Sénégal | Registre blockchain Polygon

---

## Product Identity

| Attribute | Value |
|-----------|-------|
| **Product Type** | Real Estate / Land Registry (GovTech) |
| **Tone** | Trustworthy · Professional · Transparent |
| **Keywords** | sécurité, confiance, foncier, Sénégal, innovation |
| **Style** | Minimalism + Clean Professional |
| **Platforms** | Flutter Mobile (buyers/sellers) + Angular Web Admin |

---

## Design Tokens (Cross-Platform)

### Color System

#### Semantic Palette

| Token | Hex | Usage | WCAG 4.5:1 |
|-------|-----|-------|-------------|
| `--green-900` | `#052E16` | Hero gradients, extreme emphasis | Passes on white |
| `--green-800` | `#14532D` | Primary buttons, price text, hover states | Passes on white |
| `--green-700` | `#166534` | Gradient mid-point | Passes on white |
| `--green-600` | `#16A34A` | PRIMARY — CTAs, links, active nav, success badges | 4.6:1 on white |
| `--green-500` | `#22C55E` | Icons, secondary accent | 3.2:1 — icon only |
| `--green-100` | `#DCFCE7` | Certified badges, verified backgrounds | — |
| `--green-50` | `#F0FDF4` | Table selected rows, success backgrounds | — |
| `--slate-900` | `#1E293B` | PRIMARY TEXT — headings, body | 15.3:1 on white |
| `--slate-600` | `#475569` | Secondary text, metadata | 8.6:1 on white |
| `--slate-500` | `#64748B` | Muted text, placeholders, labels | 6.2:1 on white |
| `--slate-300` | `#CBD5E1` | Disabled text, non-essential info | 4.1:1 on white |
| `--slate-200` | `#E2E8F0` | Borders, dividers, input strokes | — |
| `--slate-100` | `#F1F5F9` | Surface backgrounds, hash bg | — |
| `--slate-50` | `#F8FAFC` | PAGE BACKGROUND | — |
| `--amber-600` | `#D97706` | Pending badges, caution | 4.5:1 on white |
| `--amber-50` | `#FFFBEB` | Pending backgrounds | — |
| `--red-600` | `#DC2626` | Errors, danger actions, rejections | 5.2:1 on white |
| `--red-50` | `#FEF2F2` | Error backgrounds | — |
| `--blue-600` | `#2563EB` | Info badges, document hash | 5.5:1 on white |
| `--blue-50` | `#EFF6FF` | Info backgrounds | — |
| `--white` | `#FFFFFF` | Cards, surfaces, text on dark | — |

#### Dark Mode Tokens

| Token | Value | Notes |
|-------|-------|-------|
| `--surface-dark` | `#0F172A` | Page background (slate-950) |
| `--card-dark` | `#1E293B` | Card/surface backgrounds |
| `--border-dark` | `#334155` | Borders on dark |
| `--text-primary-dark` | `#F1F5F9` | Body text on dark |
| `--text-secondary-dark` | `#94A3B8` | Muted text on dark |
| `--green-400-dark` | `#4ADE80` | Accent on dark (increased brightness) |

### Typography

#### Font Stack

| Role | Flutter | Angular Web |
|------|---------|-------------|
| **Body** | `DM Sans` | `'Inter', system-ui, sans-serif` |
| **Display** | `DM Sans` (weight 700-900) | `'Inter', system-ui, sans-serif` |
| **Monospace** | `'SF Mono', 'Roboto Mono'` | `'JetBrains Mono', 'SF Mono', monospace` |

#### Type Scale

| Token | Size/Weight/LineH | Usage | Platform |
|-------|-------------------|-------|----------|
| `display-xl` | 34px / 900 / 1.1 | Hero title (splash) | Flutter |
| `display-lg` | 28px / 800 / 1.15 | Page title (web admin) | Both |
| `display-md` | 22px / 700 / 1.2 | Section headings, modal titles | Both |
| `display-sm` | 18px / 700 / 1.25 | Card titles, price display | Both |
| `heading` | 15px / 600 / 1.3 | Item titles, stat values | Both |
| `body` | 14px / 400 / 1.5 | PRIMARY BODY TEXT | Both |
| `body-sm` | 13px / 400 / 1.5 | Secondary content, table cells | Both |
| `caption` | 12px / 500 / 1.4 | Metadata, timestamps, badges | Both |
| `caption-sm` | 11px / 600 / 1.3 | Badge text, small labels | Both |
| `overline` | 10px / 700 / 1.2 / 1.5px LS | Labels, cert headers, hash | Both |

### Spacing Scale (4dp base)

| Token | Value | Usage |
|-------|-------|-------|
| `space-2` | 2dp | Micro spacing |
| `space-4` | 4dp | Icon-text gap, inline padding |
| `space-6` | 6dp | Small internal gaps |
| `space-8` | 8dp | Between grouped elements |
| `space-10` | 10dp | Horizontal gaps |
| `space-12` | 12dp | Section sub-spacing |
| `space-14` | 14dp | Internal card padding |
| `space-16` | 16dp | ⭐ Default content padding |
| `space-20` | 20dp | Section offset |
| `space-24` | 24dp | Major section padding |
| `space-32` | 32dp | Large sections, empty states |
| `space-40` | 40dp | Page bottom spacer |
| `space-48` | 48dp | Hero content margin |

### Corner Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 8px | Inputs, small cards |
| `radius-md` | 12px | Cards, buttons, modals |
| `radius-lg` | 16px | Cards, bottom sheets, hero |
| `radius-xl` | 20px | Badges, cert badge |
| `radius-full` | 999px | Chips, avatars, pills |

### Shadows

| Token | Value (Flutter) | Value (CSS) |
|-------|-----------------|-------------|
| `shadow-sm` | `black 8%` y:4 blur:6 | `0 1px 2px rgba(0,0,0,0.05)` |
| `shadow-md` | `black 8%` y:4 blur:10 | `0 4px 6px rgba(0,0,0,0.06)` |
| `shadow-lg` | `black 10%` y:8 blur:24 | `0 10px 24px rgba(0,0,0,0.08)` |
| `shadow-xl` | `black 25%` y:12 blur:40 | `0 20px 40px rgba(0,0,0,0.15)` |

---

## Component Design Rules

### Buttons

| Property | Primary | Secondary | Outline | Danger | Text |
|----------|---------|-----------|---------|--------|------|
| Background | `--green-800` | `--green-600` | Transparent | `--red-600` | Transparent |
| Text color | `--white` | `--white` | `--green-600` | `--white` | `--slate-900` |
| Border | None | None | `2px solid --green-600` | None | None |
| Hover | `--green-900` | `--green-700` | `+ bg --green-50` | `#B91C1C` | `--slate-100` |
| Disabled | Opacity 0.5 | Opacity 0.5 | Opacity 0.4 | Opacity 0.5 | Opacity 0.4 |
| Height | 48-56dp | 48-56dp | 48-56dp | 48-56dp | auto |
| Padding | `space-16` H | `space-16` H | `space-16` H | `space-16` H | `space-8` H |
| Radius | `radius-md` | `radius-md` | `radius-md` | `radius-md` | none |

### Navigation (Mobile — Bottom Bar)

| Property | Value |
|----------|-------|
| Height | 64dp + bottom safe area |
| Background | `--white` |
| Active icon | `--green-600` |
| Inactive icon | `--slate-500` |
| Label size | `caption` (11px) |
| Label weight | 600 active / 400 inactive |
| Icon size | 26dp |
| Gap | 4dp icon-label |
| Badge | `--red-600`, white text, 8dp radius |

### Navigation (Web Admin — Sidebar)

| Property | Value |
|----------|-------|
| Width | 260px (collapsed: 72px) |
| Background | `--slate-900` |
| Active item | `--green-400-dark` text + `rgba(74,222,128,0.12)` bg |
| Default item | `rgba(255,255,255,0.55)` text |
| Group label | `rgba(255,255,255,0.35)` uppercase |
| Padding | `space-4` top/bottom groups |

### Card

| Property | Value |
|----------|-------|
| Background | `--white` |
| Radius | `radius-md` (12px) |
| Shadow | `shadow-md` |
| Internal padding | `space-16` |
| Image radius (top) | `radius-md` top-only |

### Input Fields

| Property | Value |
|----------|-------|
| Height | 48dp |
| Border | `1.5px solid --slate-200` |
| Focus border | `1.5px solid --green-600` |
| Radius | `radius-sm` (8px) |
| Label | `body-sm` weight 600, `--slate-600` |
| Error border | `--red-600` |
| Helper | `caption` `--slate-500` |
| Padding H | `space-16` |

### Badges & Chips

| Property | Pending | Certified | Rejected | Info |
|----------|---------|-----------|----------|------|
| Background | `--amber-50` | `--green-100` | `--red-50` | `--blue-50` |
| Text color | `--amber-600` | `--green-600` | `--red-600` | `--blue-600` |
| Radius | `radius-full` | `radius-full` | `radius-full` | `radius-full` |
| Padding | `space-6 * space-12` | | | |
| Text size | `caption-sm` 600 | | | |

---

## Interaction & Motion

### Duration Tokens

| Token | Duration | Where |
|-------|----------|-------|
| `motion-instant` | 80ms | Press feedback |
| `motion-fast` | 150ms | Micro-interactions, hover |
| `motion-base` | 200ms | Card transitions, state changes |
| `motion-slow` | 300ms | Page transitions, modal open |
| `motion-enter` | 400ms | Screen entrance (splash) |

### Easing Tokens

| Token | Curve | Usage |
|-------|-------|-------|
| `ease-out` | cubic-bezier(0.0, 0.0, 0.2, 1) | Elements entering |
| `ease-in` | cubic-bezier(0.4, 0.0, 1, 1) | Elements exiting |
| `spring` | flutter: `elasticOut` / css: `cubic-bezier(0.34, 1.56, 0.64, 1)` | Hero/splash scales |
| `linear` | cubic-bezier(0, 0, 1, 1) | Progress bars only |

### Motion Rules

- **Exit faster than enter**: exits at 60% of enter duration
- **Interruptible**: user tap cancels in-progress animation
- **Opacity threshold**: never linger below 0.2 opacity on fade
- **Reduced motion**: all animations respect `prefers-reduced-motion`

---

## UX Guidelines (Priority Checklist)

### CRITICAL — Every Screen

- [ ] Touch targets ≥44×44dp (Flutter) / ≥44px (Angular)
- [ ] Visible focus rings / keyboard navigation
- [ ] min 4.5:1 contrast on all text
- [ ] SafeArea respected on all screens (notch, gesture bar)
- [ ] Loading feedback within 150ms of action
- [ ] Error messages with recovery path

### HIGH — Before Launch

- [ ] No emoji as icons (use Material Icons / SVG)
- [ ] Consistent icon family (filled vs outline per hierarchy)
- [ ] Empty states on all list screens
- [ ] Dark mode parity checked
- [ ] Responsive down to 375px width
- [ ] Locale-aware number/date formatting (fr-SN)

### MEDIUM — Tech Debt

- [ ] CSS variables replacing hardcoded hex (Angular)
- [ ] AppTheme tokens usage audit (Flutter)
- [ ] 4dp spacing scale enforcement
- [ ] Animation duration/easing tokens centralized
- [ ] Skeleton screens replacing spinners for >1s loads

---

## Platform-Specific Implementation

### Flutter (Mobile)

**Theme** → `lib/core/theme/app_theme.dart`

```
Required updates:
1. Add space tokens: static const space = _Spacing();
   class _Spacing { final x4 = 4.0; x8 = 8.0; x12 = 12.0; ... }
2. Add motion tokens: static const motion = _Motion();
   class _Motion { final fast = 150; base = 200; ... }
3. Add radius tokens: static const radius = _Radius();
4. Add dark theme: ThemeData(brightness: dark, ...)
5. Remove direct Color(0xFF...) in all screens
```

**Shared widgets audit pattern:**
```
✅ Already OK:  app_text_field.dart (tokens), gradient_button.dart (tokens)
❌ Needs fix:  parcel_card.dart (margins → space tokens)
```

### Angular (Web Admin)

**styles.scss** → Activate the design system:

```scss
// 1. Reactivate CSS variables (currently commented out)
:root { @include design-tokens(); }

// 2. Add as SCSS module:
// _tokens.scss → all color, space, radius, shadow variables
// _typography.scss → type scale classes
// _components.scss → button, card, badge, input classes

// 3. Component migration:
// Replace hardcoded hex with var(--token) in all components
// Replace inline [style] attributes with CSS classes
```

---

## Anti-Patterns to Avoid

| Anti-pattern | Why | Fix |
|-------------|-----|-----|
| `Color(0xFF0F172A)` in `certificat_screen.dart` | Bypasses theme, breaks dark mode | Use add to AppTheme |
| `Colors.grey[300]` in `shimmer_card.dart` | Inconsistent with palette | Use `AppTheme.bgLight` variant |
| `Colors.red` map marker in `publier_screen.dart` | Hardcoded non-token color | Add `AppTheme.red` or semantic `mapMarker` |
| Raw hex `#2e7d32` in Angular parcels | Duplicate green token | Use `var(--green-600)` |
| Commented-out `:root` variables in `styles.scss` | Dead code + no DS applied | Activate or remove |
| `users-list.component.ts` duplicate code block | Runtime error | Delete duplicate |
| Spacing values like 14, 10, 5, 7 | Breaks 4dp rhythm | Round to nearest 4dp multiple |

---

## Critical Fixes (from Audit)

### Flutter Mobile
1. **certificat_screen.dart:80,91** — Replace `Color(0xFF0F172A)` with new `AppTheme.surfaceDark` and `Color(0xFF4ADE80)` with `AppTheme.green400`
2. **publier_screen.dart:183** — Replace `Colors.red` with `AppTheme.red`
3. **shimmer_card.dart** — Replace `Colors.grey[300]` with `AppTheme.bgLight`
4. **All EdgeInsets** — Audit and normalize to 4dp scale (e.g., 14→12 or 16, 5→4, 7→8, 10→8 or 12)

### Angular Web Admin
1. **users-list.component.ts** — Remove duplicate code (lines 58-80)
2. **styles.scss** — Reactivate CSS custom properties as active design tokens
3. **All components** — Migrate hardcoded hex to `var(--token)` references
4. **validation.spec.ts** — Rename to reflect actual test content

---

## Version

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-05-12 | Initial master design system |
