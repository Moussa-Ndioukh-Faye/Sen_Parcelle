# Admin Dashboard — Page Design (Angular Web)

> Overrides MASTER.md for the admin panel

---

## Layout

```
┌──────────────────────────────────────────────────┐
│ ╔══════╗  ┌────────────────────────────────────┐ │
│ ║ Logo  ║  │ 🔍 Search...    🔔(7)  👤 Admin  │ │
│ ║       ║  └────────────────────────────────────┘ │
│ ║       ║  ┌────────────────────────────────────┐ │
│ ║ 📊    ║  │                                    │ │
│ ║   Dsh │  │                                    │ │
│ ║ 🏠    ║  │        Content Area                │ │
│ ║   Pcl │  │         (router-outlet)             │ │
│ ║ ✅   ║  │                                    │ │
│ ║   Val │  │                                    │ │
│ ║ 👥   ║  │                                    │ │
│ ║   Usr │  └────────────────────────────────────┘ │
│ ║ 🔗   ║                                         │
│ ║   Bc  │                                         │
│ ║       │                                         │
│ ║ ◀    │                                         │
│ ╚══════╝                                         │
└──────────────────────────────────────────────────┘
   260px                   rest
```

---

## Dashboard Page

### Stats Grid

```
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ 🏠    │ │ ✅   │ │ ⏳   │ │ 🔗   │
│ 1.234 │ │ 892  │ │ 12   │ │ 456  │
│ TOT.  │ │ CERT.│ │ EN   │ │ BC   │
│ Pcls  │ │      │ │ ATT. │ │ TX   │
│ Voir→ │ │ Voir→│ │      │ │      │
└──────┘ └──────┘ └──────┘ └──────┘
```

| Stat Card | Top Border | Icon |
|-----------|-----------|------|
| Total Parcelles | `--amber-600` | `Icons.home` |
| Certifiées | `--green-600` | `Icons.verified` |
| En Attente | `--blue-600` | `Icons.hourglass_empty` |
| Transactions BC | `--purple-700` | `Icons.link` |

### Dashboard Grid Layout

```
┌─────────────────────┐ ┌─────────────────────┐
│ 📋 Parcelles        │ │ 📈 Activité         │
│ récentes            │ │ récente             │
│                     │ │                     │
│ ┌─────────────────┐ │ │ ● Parcelle 123      │
│ │ Titre     2.5M  │ │ │   certifiée    2min │
│ │ Dakar   certifié│ │ │ ● Paiement reçu     │
│ ├─────────────────┤ │ │   #456         15min │
│ │ Titre     1.8M  │ │ │ ● KYC refusé   1h  │
│ │ Thiès   en att. │ │ │                     │
│ └─────────────────┘ │ └─────────────────────┘
│ [Voir tout →]       │
└─────────────────────┘
```

---

## Validation Page (Admin)

| Column | Width | Align |
|--------|-------|-------|
| Propriétaire/Email | 25% | Left |
| Localisation | 12% | Left |
| Prix | 12% | Right |
| Date | 15% | Left |
| Document | 18% | Left |
| Actions | 18% | Right |

### Modal: Parcel Detail

```
┌─────────────────────────────────────┐
│ Détails de la parcelle          ✕  │
├─────────────────────────────────────┤
│ Propriétaire:  Moussa Faye          │
│ Email:         moussa@email.com     │
│ Localisation:  Dakar, Almadies      │
│ Superficie:    500 m²               │
│ Prix:          5 000 000 FCFA       │
│ Type:          Terrain urbain       │
│                                     │
│ 🔗 Hash document                    │
│ 0x7a9f...b3e2                       │
│                                     │
│ [   Refuser  ]  [ ✅ Approuver   ]  │
└─────────────────────────────────────┘
```

---

## Blockchain Page

| Feature | Rule |
|---------|------|
| Network indicator | Green pulsing dot + "Polygon Mainnet" |
| Stats cards | 4-column: Total registré, Dernier bloc, Contrats, Wallet |
| Verifier | Input field + button + result (green/red) |
| Transaction list | Table with hash, date, explorer link |

### Component: Blockchain Verifier

```
┌──────────────────────────────────┐
│ 🔍 Vérifier un document          │
│                                  │
│ ┌────────────────────┐           │
│ │ Hash du document   │ [Vérifier]│
│ └────────────────────┘           │
│                                  │
│ ✅ Document valide — Parcelle #42│
│   Propriétaire: 0x7a9f...b3e2   │
│   Date: 12/05/2026               │
└──────────────────────────────────┘
```
