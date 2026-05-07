# 🏡 Sen_parcelle — Plateforme Foncière Sécurisée · Sénégal

> Architecture Microservices · Django 5 · Flutter · Angular 17 · Polygon Blockchain

---

## 📦 Structure du Projet

```
SEN_PARCELLE/
│
├── backend/                        ← API Django (Python 3.11+)
│   ├── core/                       # BaseModel, Exceptions, RBAC, Crypto
│   │   ├── models/base.py          # UUID + SoftDelete + Timestamps
│   │   ├── exceptions/base.py      # Domain + App exceptions + DRF handler
│   │   ├── permissions/rbac.py     # 11 permissions (IsAdmin, CanPublishParcel...)
│   │   └── utils/crypto.py         # SHA-256, Validators SN, RateLimit, SecurityHeaders
│   ├── config/
│   │   └── settings/               # base.py + development.py + test.py
│   ├── apps/
│   │   ├── users/                  # Domaine Utilisateurs — 15 fichiers
│   │   │   ├── domain/             # UserEntity, Email, PhoneNumber, DocumentHash, IuserRepository
│   │   │   ├── infrastructure/     # ORM Django + DjangoUserRepository + SMS adapters (Twilio, Orange)
│   │   │   ├── application/
│   │   │   │   ├── use_cases/      # RegisterUseCase, LoginUseCase (2FA OTP), VerifyKYCUseCase
│   │   │   │   └── services/       # JWTService, OTPService, KYCService, AuthService
│   │   │   ├── presentation/       # AuthViewSet, UserViewSet
│   │   │   └── tests/              # 51 tests (domain + security)
│   │   ├── parcels/                # Domaine Parcelles — 10 fichiers
│   │   │   ├── domain/             # ParcelEntity, GeoPoint, ParcelStatus, IParcelRepository
│   │   │   ├── infrastructure/     # ORM PostGIS (Parcel, ParcelPhoto) + DjangoParcelRepository
│   │   │   ├── application/        # SubmitParcel, ValidateParcel, SearchParcels (anti-fraude 50m)
│   │   │   └── presentation/       # ParcelViewSet + Serializers + DI
│   │   ├── transactions/           # Domaine Transactions — 13 fichiers
│   │   │   ├── domain/             # TransactionEntity, TransactionStatus, PaymentProvider
│   │   │   ├── infrastructure/     # ORM + WaveAdapter + OrangeMoneyAdapter + factory
│   │   │   ├── application/        # InitiatePayment, ConfirmPayment (webhook + signature HMAC)
│   │   │   ├── presentation/       # TransactionViewSet + DI
│   │   │   └── tests/              # 18 tests
│   │   ├── blockchain/             # Blockchain — 4 fichiers
│   │   │   ├── tasks.py            # Celery: certify_parcel, transfer_ownership, SMS, push, report
│   │   │   └── application/services/blockchain_service.py  # Orchestration IPFS + Polygon
│   │   │   └── infrastructure/adapters/
│   │   │       ├── polygon_adapter.py  # web3.py: registerParcel, transferOwnership, verifyDocument
│   │   │       └── ipfs_adapter.py     # Pinata API: pin/unpin metadata
│   │   ├── audit/                  # Audit — 3 fichiers
│   │   │   ├── models.py           # AuditLog immuable (20 types d'actions) + hash intégrité
│   │   │   ├── services.py         # AuditService: log, historique, événements sécurité
│   │   │   └── middleware.py       # AuditMiddleware: auto-log requêtes sensibles
│   │   └── notifications/          # ⚠️ Module vide — NotificationService introuvable
│   ├── infrastructure/
│   │   ├── celery/app.py           # Configuration Celery
│   │   └── storage/s3.py           # S3StorageService (upload public/privé + URLs signées)
│   └── manage.py
│
├── mobile/                         ← Application Flutter (Riverpod)
│   ├── lib/
│   │   ├── main.dart               # App bootstrap + Theme + GoRouter + ProviderScope
│   │   ├── core/
│   │   │   ├── network/            # DioClient + JWTInterceptor + RetryInterceptor + Result<T>
│   │   │   └── theme/              # AppTheme (Material 3 + palette verte)
│   │   ├── features/
│   │   │   ├── auth/               # Login + Register + OTP + Splash screens + providers
│   │   │   ├── parcels/            # Home + Explore + Detail + Publier + Certificat + providers
│   │   │   ├── transactions/       # Models + Repository + providers
│   │   │   ├── profile/            # Profile + KYC screens
│   │   │   └── messages/           # Messages (démo uniquement)
│   │   └── shared/widgets/         # ParcelCard + GradientButton + MainShell + Shimmer
│   ├── test/
│   │   └── auth_provider_test.dart # 9 tests (AuthNotifier + ParcelModel + ApiException)
│   └── pubspec.yaml
│
├── web/                            ← Dashboard Admin Angular 17 (Signals)
│   └── src/app/
│       ├── core/
│       │   ├── models/index.ts     # Interfaces TypeScript + ApiService
│       │   ├── services/auth.service.ts  # Signals-based auth
│       │   ├── interceptors/jwt.interceptor.ts  # Auto-refresh token
│       │   └── guards/auth.guard.ts       # authGuard + adminGuard + guestGuard
│       ├── features/
│       │   ├── auth/               # LoginComponent (gradient, validation réactive)
│       │   ├── dashboard/          # Stats temps réel + Activité récente + DashboardService
│       │   ├── parcels/            # ParcelsService + ValidationComponent (valider/rejeter)
│       │   ├── users/              # UsersService + KYCManagerComponent (approve/reject + tabs)
│       │   └── blockchain/         # Certificats Polygon + Vérificateur par hash
│       └── shared/components/layout/  # Sidebar + Header + Navigation
│
├── blockchain/                     ← Smart Contract Solidity + Hardhat
│   ├── contracts/
│   │   └── SenParcelle.sol         # Registre foncier immuable (307 lignes)
│   ├── test/
│   │   └── SenParcelle.test.js     # 16 tests (déploiement, register, transfer, verify, pause)
│   ├── scripts/
│   │   └── deploy.js               # Déploiement Mumbai/Polygon + sauvegarde artifacts
│   └── hardhat.config.js           # Solidity 0.8.20 + optimizer + networks
│
└── infra/
    └── docker/
        └── docker-compose.yml      # Production stack (PostGIS + Redis + Django + Celery + Nginx)
```

---

## 🚀 Démarrage rapide

### Backend Django
```bash
cd backend
pip install poetry
poetry install
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Mobile Flutter
```bash
cd mobile
flutter pub get
flutter run
# Ou pour Android: flutter run --dart-define=API_URL=http://10.0.2.2:8000/api
```

### Admin Angular
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

### Docker (tout en un)
```bash
docker-compose -f infra/docker/docker-compose.yml up --build
```

---

## 🔐 Sécurité implémentée

| Mécanisme         | Détail                                              | Statut |
|-------------------|-----------------------------------------------------|--------|
| JWT               | Access 15min + Refresh 7j + Blacklist Redis         | ✅     |
| OTP 2FA           | 6 chiffres · 5min · 3 tentatives max · Redis        | ✅     |
| KYC               | CNI/Passeport · Hash SHA-256 · S3 chiffré           | ✅     |
| Brute force       | Lockout 30min après 5 tentatives                    | ✅     |
| Rate limiting     | Fenêtre glissante Redis (API + Auth séparés)        | ✅     |
| RBAC              | Acheteur / Vendeur / Admin (11 permissions)         | ✅     |
| Anti-fraude       | Détection doublons géographiques PostGIS (50m)      | ✅     |
| Blockchain        | Hash SHA-256 → IPFS → Polygon (immuable)            | ✅     |
| Audit             | Logs immuables + hash intégrité + middleware auto   | ✅     |
| CSP Headers       | SecurityHeadersMiddleware (CSP, HSTS, X-Frame)      | ✅     |

---

## 🗄️ API Endpoints

### Authentification
| Méthode | Endpoint | Permission | Description |
|---------|----------|------------|-------------|
| POST | `/api/auth/inscription/` | Public (10/min) | Inscription utilisateur |
| POST | `/api/auth/login/` | Public (5/min) | Connexion + 2FA OTP |
| POST | `/api/auth/refresh/` | Public | Refresh JWT token |

### Utilisateurs
| Méthode | Endpoint | Permission | Description |
|---------|----------|------------|-------------|
| GET | `/api/utilisateurs/moi/` | Authenticated | Profil courant |
| POST | `/api/utilisateurs/{id}/kyc/` | Admin | Validation KYC |

### Parcelles
| Méthode | Endpoint | Permission | Description |
|---------|----------|------------|-------------|
| GET | `/api/parcelles/` | Public | Recherche avec filtres |
| GET | `/api/parcelles/{id}/` | Public | Détail parcelle |
| POST | `/api/parcelles/` | Vendeur + KYC | Soumettre parcelle |
| POST | `/api/parcelles/{id}/valider/` | Admin | Valider/rejeter |
| GET | `/api/parcelles/mes-parcelles/` | Vendeur | Mes parcelles |

### Transactions
| Méthode | Endpoint | Permission | Description |
|---------|----------|------------|-------------|
| POST | `/api/transactions/initier/` | Acheteur + KYC + 2FA (3/min) | Initier paiement Wave/OM |
| POST | `/api/transactions/webhook/{provider}/` | Public | Webhook paiement |
| GET | `/api/transactions/mes-achats/` | Authenticated | Mes achats |
| GET | `/api/transactions/mes-ventes/` | Authenticated | Mes ventes |

---

## 🔗 Blockchain — Smart Contract

**Contrat** : `SenParcelle.sol` (Solidity 0.8.20, déployé sur Polygon)

### Fonctions principales

| Fonction | Accès | Description |
|----------|-------|-------------|
| `registerParcel()` | Admin only | Enregistrer une parcelle certifiée (hash + IPFS) |
| `transferOwnership()` | Admin only | Transférer la propriété après paiement confirmé |
| `updateMetadata()` | Admin only | Mettre à jour le CID IPFS |
| `revokeParcel()` | Admin only | Révoquer (fraude détectée) |
| `verifyDocument()` | Public (view) | Vérifier un hash de document (gratuit) |
| `getParcel()` | Public (view) | Infos complètes d'une parcelle |
| `getParcelHistory()` | Public (view) | Historique des propriétaires |
| `getOwnerParcels()` | Public (view) | Parcelles d'un propriétaire |
| `pause()` / `unpause()` | Admin only | Emergency pause |

### Tests : 16 tests couvrant
- Déploiement (owner, paused, counters)
- Enregistrement (succès, doublons, accès, address(0))
- Transfert (succès, historique, isOwner, mêmes owner, révoqué)
- Vérification (valide, inconnu, révoqué)
- Pause (admin only, blocage register)

### Réseaux supportés
| Réseau | Chain ID | Usage |
|--------|----------|-------|
| Hardhat | 31337 | Tests locaux |
| Mumbai (Polygon testnet) | 80001 | Tests |
| Polygon mainnet | 137 | Production |

---

## 📊 Couverture des tests

| Module | Fichiers de test | Nombre de tests | Couverture fonctionnelle |
|--------|-----------------|-----------------|-------------------------|
| **Backend — Users** | `test_domain.py`, `test_security.py` | 51 | Domain entities, value objects, JWT, OTP, Crypto, Validators, RateLimit, RegisterUseCase |
| **Backend — Parcels** | Aucun dédié | 5 (dans users/test_domain.py) | ParcelEntity, GeoPoint seulement |
| **Backend — Transactions** | `test_payment.py` | 18 | TransactionEntity, WaveAdapter, InitiatePayment, ConfirmPayment |
| **Backend — Blockchain** | Aucun | 0 | — |
| **Backend — Audit** | Aucun | 0 | — |
| **Backend — Notifications** | Aucun | 0 | Module vide |
| **Blockchain (Solidity)** | `SenParcelle.test.js` | 16 | Deployment, register, transfer, verify, pause |
| **Mobile (Flutter)** | `auth_provider_test.dart` | 9 | AuthNotifier, ParcelModel, ApiException |
| **Web (Angular)** | `validation.spec.ts` | ~4 | ValidationComponent, ParcelsService |
| **TOTAL** | **6 fichiers** | **~103 tests** | |

---

## 🏗️ Architecture

### Pattern : Clean Architecture / Hexagonale

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

### Stack technique complète

| Couche | Technologie |
|--------|-------------|
| **Backend API** | Django 5.0 + DRF 3.15 |
| **Base de données** | PostgreSQL 16 + PostGIS 3.4 |
| **Cache/Queue** | Redis 7 + Celery 5.3 |
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

## ⚠️ Problèmes connus et dette technique

### 🔴 Bugs critiques (bloquants)

1. **`NotificationService` introuvable** — Le module `apps/notifications/services/` est vide mais la classe est importée dans `di.py`, `submit_parcel.py`, `kyc_service.py`, `tasks.py`. **Impact : ImportError à l'exécution.**

2. **Imports cassés dans `di.py`** — `LoginUseCase` et `VerifyKYCUseCase` sont importés depuis `register.py` (ligne 78, 89) mais définis dans `login.py` et `verify_kyc.py`. **Impact : ImportError à l'exécution.**

3. **Composants Angular manquants** — 4 fichiers référencés dans le routing n'existent pas :
   - `features/auth/auth.routes.ts`
   - `features/parcels/components/parcels-list.component.ts`
   - `features/parcels/components/parcel-detail.component.ts`
   - `features/users/components/users-list.component.ts`
   **Impact : Crash au runtime sur ces routes.**

4. **Imports Flutter cassés** — `parcel_detail_screen.dart` importe un fichier thème inexistant, `kyc_screen.dart` importe `shared_widgets.dart` qui n'existe pas. **Impact : Erreur de compilation Flutter.**

5. **Double définition `authStateProvider`** — Défini à la fois dans `dio_client.dart` et `main.dart` du Flutter. **Impact : Conflit Riverpod.**

### 🟡 Avertissements

6. **Pas de migrations Django générées** — Aucun fichier de migration trouvé dans le repository.
7. **Pas de fichier `wsgi.py`** — Requis pour le déploiement Gunicorn (référencé dans docker-compose).
8. **Pas de fichier `.apps.py`** — Aucune app Django n'a de configuration explicite.
9. **Duplication de code** — `users/presentation/views.py` et `parcels/presentation/views.py` contiennent tous deux les ViewSets Auth et User.
10. **`ApiService` dans `models/index.ts`** — Mélange de responsabilités dans le code Angular.
11. **Dockerfile et nginx.conf commentés** — Dans `docker-compose.yml`, le Dockerfile backend et la config Nginx sont en commentaires.
12. **Pas de fichier de production settings** — Le docker-compose référence `config.settings.production` qui n'existe pas.

### 🟢 À implémenter (Roadmap)

13. **Paiement Wave/Orange Money** — Intégration côté mobile (écrans de paiement) et webhooks
14. **Carte GPS Flutter** — Intégrer `flutter_map` dans `publier_screen.dart` (actuellement placeholder)
15. **Messages temps réel** — Remplacer les données démo par WebSocket ou API
16. **KYC Flutter** — Connecter l'upload réel de documents à l'API
17. **Tests backend** — Blockchain, Audit, ViewSets, repositories, services complexes
18. **CI/CD** — Le workflow GitHub Actions est commenté dans `docker-compose.yml`

---

## 🔑 Variables d'environnement requises

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

## 📝 Licence

Projet Sen_parcelle — Plateforme foncière sécurisée pour le Sénégal.
