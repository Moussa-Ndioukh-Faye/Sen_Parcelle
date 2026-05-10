# Sen_parcelle — Plateforme Foncière Sécurisée · Sénégal

> Architecture Microservices — Django 5 · Flutter · Angular 17 · Polygon Blockchain

![Status](https://img.shields.io/badge/status-en%20d%C3%A9veloppement-yellow)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Django](https://img.shields.io/badge/django-5.0-green)
![Flutter](https://img.shields.io/badge/flutter-3.2%2B-blue)
![Angular](https://img.shields.io/badge/angular-17-red)
![Solidity](https://img.shields.io/badge/solidity-0.8.20-purple)
![License](https://img.shields.io/badge/licence-MIT-green)

---

**Sen_parcelle** est une plateforme foncière numérique sécurisée pour le Sénégal. Elle permet l'enregistrement, la certification et le transfert de propriété de parcelles via un système décentralisé sur la blockchain Polygon, avec vérification KYC, paiements mobile money (Wave / Orange Money) et un tableau de bord administrateur complet.

---

## Table des matières

- [Architecture](#architecture)
- [Structure du projet](#structure-du-projet)
- [Stack technique](#stack-technique)
- [Prérequis](#prérequis)
- [Démarrage rapide](#démarrage-rapide)
- [Tests](#tests)
- [Sécurité](#sécurité)
- [API](#api)
- [Smart Contract](#smart-contract)
- [Contribuer](#contribuer)
- [Problèmes connus](#problèmes-connus)
- [Variables d'environnement](#variables-denvironnement)
- [Licence](#licence)

---

## Architecture

### Clean Architecture / Hexagonale

```
┌─────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                      │
│  ViewSets DRF / Serializers  │  Flutter Screens     │
│  Angular Components          │  GoRouter            │
├─────────────────────────────────────────────────────┤
│              APPLICATION LAYER                       │
│  Use Cases  │  Services  │  DI (lru_cache factories)│
├─────────────────────────────────────────────────────┤
│              DOMAIN LAYER                            │
│  Entities (dataclasses)  │  Repository Interfaces   │
│  Value Objects (immutable) │  Business Rules        │
├─────────────────────────────────────────────────────┤
│              INFRASTRUCTURE LAYER                    │
│  Django ORM  │  PostGIS  │  Adapters (Wave, OM)    │
│  S3 Storage  │  Polygon (web3)  │  IPFS (Pinata)  │
│  Redis  │  Celery  │  Twilio/Orange SMS            │
└─────────────────────────────────────────────────────┘
```

### Flux de certification blockchain

```
1. Vendeur soumet parcelle → SubmitParcelUseCase
   ├─ Vérification KYC vendeur
   ├─ Détection anti-fraude géographique (PostGIS 50m)
   ├─ Hash SHA-256 du document
   └─ Upload S3 du document

2. Admin valide → ValidateParcelUseCase
   └─ Trigger Celery task: certify_parcel_on_blockchain
       ├─ Upload metadata IPFS (Pinata)
       ├─ Conversion UUID → uint256 (Solidity)
       ├─ PolygonAdapter.registerParcel()
       └─ Mise à jour: status=CERTIFIED + tx_hash

3. Acheteur paie → InitiatePaymentUseCase (Wave/Orange Money)
   └─ Webhook confirme → ConfirmPaymentUseCase
       └─ Trigger Celery: transfer_ownership_on_blockchain
           └─ PolygonAdapter.transferOwnership()
```

---

## Structure du projet

```
SEN_PARCELLE/
│
├── backend/                          ← API Django REST (Python 3.11+)
│   ├── core/                         # BaseModel, Exceptions, RBAC, Crypto
│   ├── config/settings/              # base.py + development.py + test.py
│   ├── apps/
│   │   ├── users/                    # Auth, KYC, OTP 2FA — 15 fichiers
│   │   ├── parcels/                  # Parcelles, PostGIS, anti-fraude — 10 fichiers
│   │   ├── transactions/             # Wave, Orange Money — 13 fichiers
│   │   ├── blockchain/               # Certification Polygon — 4 fichiers
│   │   ├── audit/                    # Audit trail immuable — 3 fichiers
│   │   └── notifications/            # ⚠️ Module vide (WIP)
│   └── infrastructure/
│       ├── celery/app.py             # Celery + beat schedule
│       └── storage/s3.py             # S3UploadService
│
├── mobile/                           ← Application Flutter (Riverpod)
│   └── lib/
│       ├── core/network/             # DioClient, JWT, Result<T>
│       ├── core/theme/               # Material 3
│       ├── features/                 # Auth, Parcels, Transactions, Profile, Messages
│       └── shared/widgets/           # ParcelCard, GradientButton, Shimmer
│
├── web/                              ← Dashboard Admin Angular 17
│   └── src/app/
│       ├── core/                     # Models, Services, Interceptors, Guards
│       ├── features/                 # Auth, Dashboard, Parcels, Users, Blockchain
│       └── shared/components/layout/ # Sidebar, Header, Navigation
│
├── blockchain/                       ← Smart Contract Solidity + Hardhat
│   ├── contracts/SenParcelle.sol     # Registre foncier immuable
│   ├── test/SenParcelle.test.js      # 16 tests
│   └── scripts/deploy.js
│
└── infra/docker/
    └── docker-compose.yml            # PostGIS + Redis + Django + Celery + Nginx
```

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| **Backend API** | Django 5.0 + DRF 3.15 |
| **Base de données** | PostgreSQL 16 + PostGIS 3.4 |
| **Cache / Queue** | Redis 7 + Celery 5.3 |
| **Auth** | SimpleJWT + OTP 2FA |
| **Blockchain** | Polygon (web3.py 6.15) + IPFS (Pinata) |
| **Smart Contract** | Solidity 0.8.20 + Hardhat 2.22 |
| **Paiements** | Wave Sénégal + Orange Money |
| **SMS** | Twilio + Orange SMS Sénégal |
| **Stockage** | AWS S3 (boto3) |
| **Mobile** | Flutter 3.2+ (Riverpod + Dio + GoRouter) |
| **Web Admin** | Angular 17 (Signals + Chart.js + Leaflet) |
| **Infra** | Docker Compose + Nginx + Gunicorn |

---

## Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- Python 3.11+ et [Poetry](https://python-poetry.org/)
- Flutter 3.2+ et Dart 3.2+
- Node.js 18+ et npm
- PostgreSQL 16+ avec PostGIS (ou SQLite pour le développement)
- Redis 7
- Docker & Docker Compose (optionnel, pour l'environnement complet)

---

## Démarrage rapide

### Backend Django

```bash
cd backend
pip install poetry
poetry install
cp .env.example .env
# Éditez .env avec vos configurations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Mobile Flutter

```bash
cd mobile
flutter pub get
flutter run
# Pour Android avec l'émulateur :
flutter run --dart-define=API_URL=http://10.0.2.2:8000/api
```

### Dashboard Admin Angular

```bash
cd web
npm install
npm start
# Ouvrir http://localhost:4200
```

### Blockchain (tests)

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat test
```

### Docker (tout l'environnement)

```bash
docker-compose -f infra/docker/docker-compose.yml up --build
```

### Scripts utiles

| Commande | Description |
|----------|-------------|
| `pytest` | Lancer les tests backend |
| `python manage.py spectacular --file schema.yml` | Générer le schéma OpenAPI |
| `npm run build` | Build Angular production |
| `flutter build apk` | Build Flutter Android |
| `npx hardhat coverage` | Couverture des tests Solidity |

---

## Tests

| Module | Fichiers | Tests | Couverture |
|--------|----------|-------|------------|
| **Backend — Users** | `test_domain.py`, `test_security.py` | 51 | Domain entities, JWT, OTP, Crypto, Validators, Use Cases |
| **Backend — Transactions** | `test_payment.py` | 18 | Entities, WaveAdapter, InitiatePayment, ConfirmPayment |
| **Blockchain (Solidity)** | `SenParcelle.test.js` | 16 | Deploy, register, transfer, verify, pause |
| **Mobile (Flutter)** | `auth_provider_test.dart` | 9 | AuthNotifier, ParcelModel, ApiException |
| **Web (Angular)** | `validation.spec.ts` | ~4 | ValidationComponent, ParcelsService |
| **TOTAL** | **6 fichiers** | **~103 tests** | |

---

## Sécurité

| Mécanisme | Détail |
|-----------|--------|
| JWT | Access 15min + Refresh 7j + Blacklist Redis |
| OTP 2FA | 6 chiffres · 5min · 3 tentatives max · Redis |
| KYC | CNI/Passeport · Hash SHA-256 · S3 chiffré |
| Brute force | Lockout 30min après 5 tentatives |
| Rate limiting | Fenêtre glissante Redis (API + Auth séparés) |
| RBAC | Acheteur / Vendeur / Admin (11 permissions) |
| Anti-fraude | Détection doublons géographiques PostGIS (50m) |
| Blockchain | Hash SHA-256 → IPFS → Polygon (immuable) |
| Audit | Logs immuables + hash intégrité + middleware auto |
| CSP Headers | SecurityHeadersMiddleware (CSP, HSTS, X-Frame) |

---

## API

### Authentification

| Méthode | Endpoint | Accès |
|---------|----------|-------|
| POST | `/api/auth/inscription/` | Public (10/min) |
| POST | `/api/auth/login/` | Public (5/min) |
| POST | `/api/auth/refresh/` | Public |

### Utilisateurs

| Méthode | Endpoint | Accès |
|---------|----------|-------|
| GET | `/api/utilisateurs/moi/` | Authenticated |
| POST | `/api/utilisateurs/{id}/kyc/` | Admin |

### Parcelles

| Méthode | Endpoint | Accès |
|---------|----------|-------|
| GET | `/api/parcelles/` | Public |
| GET | `/api/parcelles/{id}/` | Public |
| POST | `/api/parcelles/` | Vendeur + KYC |
| POST | `/api/parcelles/{id}/valider/` | Admin |

### Transactions

| Méthode | Endpoint | Accès |
|---------|----------|-------|
| POST | `/api/transactions/initier/` | Acheteur + KYC + 2FA (3/min) |
| POST | `/api/transactions/webhook/{provider}/` | Public |
| GET | `/api/transactions/mes-achats/` | Authenticated |
| GET | `/api/transactions/mes-ventes/` | Authenticated |

---

## Smart Contract

**Contrat :** `SenParcelle.sol` (Solidity 0.8.20, déployé sur Polygon)

| Fonction | Accès | Description |
|----------|-------|-------------|
| `registerParcel()` | Admin | Enregistrer une parcelle certifiée |
| `transferOwnership()` | Admin | Transférer la propriété |
| `updateMetadata()` | Admin | Mettre à jour le CID IPFS |
| `revokeParcel()` | Admin | Révoquer (fraude détectée) |
| `verifyDocument()` | Public | Vérifier un hash de document |
| `getParcel()` | Public | Infos complètes d'une parcelle |
| `getParcelHistory()` | Public | Historique des propriétaires |
| `getOwnerParcels()` | Public | Parcelles d'un propriétaire |
| `pause()` / `unpause()` | Admin | Emergency pause |

**Réseaux supportés :** Hardhat (31337) · Mumbai (80001) · Polygon (137)

---

## Contribuer

Les contributions sont les bienvenues ! Voici comment procéder :

### Processus

1. **Fork** le projet et créez votre branche : `git checkout -b feature/ma-feature`
2. **Committez** vos changements : `git commit -m 'feat: ajout de ma fonctionnalité'`
3. **Push** vers la branche : `git push origin feature/ma-feature`
4. **Ouvrez une Pull Request**

### Conventions de commit

Ce projet suit la convention [Conventional Commits](https://www.conventionalcommits.org/) :

- `feat:` — Nouvelle fonctionnalité
- `fix:` — Correction de bug
- `docs:` — Documentation
- `refactor:` — Refactoring
- `test:` — Tests
- `chore:` — Maintenance
- `security:` — Sécurité

### Conventions de code

- **Backend :** Suivez les conventions PEP 8 et les patterns Clean Architecture existants
- **Flutter :** Suivez le style Dart avec `flutter analyze`
- **Angular :** Utilisez les standalone components et les Signals
- **Solidity :** Suivez les recommandations de la documentation Solidity
- **Tests :** Tout nouveau code doit être accompagné de tests

### Rapport de bugs

Utilisez les [GitHub Issues](https://github.com/Moussa-Ndioukh-Faye/Sen_Parcelle/issues) pour signaler un bug. Incluez :
- La description du bug
- Les étapes pour reproduire
- Le comportement attendu vs réel
- Les logs d'erreur si disponibles

---

## Problèmes connus

### 🔴 Bugs critiques

1. **NotificationService introuvable** — Module `apps/notifications/services/` vide mais importé dans `di.py`, `submit_parcel.py`, `kyc_service.py`, `tasks.py`
2. **Imports cassés dans `di.py`** — `LoginUseCase` et `VerifyKYCUseCase` importés depuis les mauvais modules
3. **Composants Angular manquants** — 4 fichiers référencés dans le routing n'existent pas
4. **Imports Flutter cassés** — Fichiers manquants dans `parcel_detail_screen.dart` et `kyc_screen.dart`
5. **Double définition `authStateProvider`** — Conflit Riverpod dans `dio_client.dart` et `main.dart`

### 🟡 Avertissements

6. Pas de migrations Django générées
7. Pas de fichier `wsgi.py` pour Gunicorn
8. Pas de configuration explicite `.apps.py`
9. Duplication de code dans `users/presentation/views.py` et `parcels/presentation/views.py`
10. Dockerfile et nginx.conf commentés dans docker-compose
11. Pas de fichier `settings.production.py`

### 🟢 Roadmap

12. Intégration paiement mobile (Wave/Orange Money)
13. Carte GPS Flutter
14. Messagerie temps réel (WebSocket)
15. Upload KYC mobile
16. Tests backend supplémentaires
17. CI/CD (GitHub Actions)

---

## Variables d'environnement

### Backend (`.env`)

```bash
SECRET_KEY=
DEBUG=True
DB_NAME=sen_parcelle
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
REDIS_URL=redis://localhost:6379/0

# Blockchain
POLYGON_RPC_URL=
POLYGON_PRIVATE_KEY=
POLYGON_CONTRACT_ADDRESS=
POLYGONSCAN_API_KEY=

# IPFS
PINATA_JWT=
IPFS_GATEWAY=https://gateway.pinata.cloud/ipfs

# Paiements
WAVE_API_KEY=
WAVE_SECRET_KEY=
ORANGE_MONEY_CLIENT_ID=
ORANGE_MONEY_CLIENT_SECRET=
ORANGE_MONEY_MERCHANT_KEY=

# SMS
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_BUCKET=
AWS_REGION=eu-west-1
```

### Blockchain (`.env`)

```bash
POLYGON_PRIVATE_KEY=0x...
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
POLYGONSCAN_API_KEY=
```

---

## Licence

MIT — Projet Sen_parcelle. Plateforme foncière sécurisée pour le Sénégal.
