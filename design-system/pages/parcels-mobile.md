# Parcels — Page Design (Flutter Mobile)

> Overrides MASTER.md for the core buyer flow

---

## Home Screen (Explore)

| Element | Rule | Token |
|---------|------|-------|
| Hero header | Gradient `green-900 → green-700` | `--green-900`, `--green-700` |
| Search bar | Frosted glass effect (white 0.15) | `--white` with opacity |
| Section title "Parcelles certifiées" | `display-sm` (17px) weight 800 | See type scale |
| Parcel card grid | 2 columns, gap 12dp | `space-12` |
| Avatar | `radius-full`, `--white24` bg | — |
| Shimmer | 2-column skeleton cards | `--slate-100` |

### Component: ParcelCard

```
┌──────────────────────┐
│ 🏠  Image (3:2)     │  radius-md top
│   [Certified ✔]     │  badge overlay
├──────────────────────┤
│ Titre de la parcelle │  heading (15px/700)
│ 📍 Dakar, Almadies   │  caption (12px)
│                      │
│ 5 000 000 FCFA       │  display-sm (18px/900) green-800
│ ┌──────┐ ┌────────┐  │
│ │ 500m²│ │ Terrain │  │  caption-sm chips
│ └──────┘ └────────┘  │
└──────────────────────┘
```

### Component: ParcelDetail

```
┌──────────────────────────┐
│ 🏠 Image (hero, full-w) │  SliverAppBar 240px
│   📍 Dakar, Almadies     │  location row
│   5 000 000 FCFA         │  display-lg (28px/900)
│                           │
│ ┌────┐ ┌────┐ ┌───────┐  │
│ │500m²│ │Urb.│ │Certifié│  │  metric chips
│ └────┘ └────┘ └───────┘  │
│                           │
│ ╔══════════════════════╗  │
│ ║ 🔗 Propriété         ║  │  Cert badge card
│ ║    vérifiée sur      ║  │  green gradient bg
│ ║    blockchain        ║  │  monospace hash
│ ╚══════════════════════╝  │
│                           │
│ Description...            │  body (14px)
│                           │
│ ┌──────────────────────┐  │
│ │ Vendeur vérifié 👤   │  │  seller card
│ │ Contacter           │  │
│ └──────────────────────┘  │
│                           │
│ [   Acheter maintenant  ] │  sticky bottom CTA
└──────────────────────────┘
```

---

## Publier (Publish Parcel)

| Element | Rule |
|---------|------|
| Form layout | Single column, `space-16` between fields |
| Map preview | 300px height, `radius-md`, `--slate-200` border |
| Price input | With FCFA suffix |
| Submit | Primary button (full width) |

---

## Transaction Flow

| Step | Screen | Notes |
|------|--------|-------|
| 1 | Parcel detail → "Acheter" | Bottom sheet payment method picker |
| 2 | Wave / Orange Money selection | Logo + provider name |
| 3 | Payment initiated | Loading overlay |
| 4 | Confirmation | Success state with cert link |
