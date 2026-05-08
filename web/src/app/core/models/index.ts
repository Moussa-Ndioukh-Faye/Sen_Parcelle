// ═══════════════════════════════════════════════════════════════
// src/app/core/models/index.ts
// Tous les modèles TypeScript de Sen_parcelle Admin
// ═══════════════════════════════════════════════════════════════

// ─── Utilisateur ───
export type UserRole    = 'acheteur' | 'vendeur' | 'admin';
export type KYCStatus   = 'pending' | 'verified' | 'rejected';

export interface User {
  id:             string;
  nom:            string;
  email:          string;
  telephone:      string;
  role:           UserRole;
  kyc_status:     KYCStatus;
  is_2fa_enabled: boolean;
  is_active:      boolean;
  created_at:     string;
}

export interface UserDetail extends User {
  kyc_document_hash?: string;
  kyc_verified_at?:   string;
  failed_attempts:    number;
  locked_until?:      string;
}

// ─── Parcelle ───
export type ParcelStatus = 'pending' | 'validated' | 'certified' | 'rejected' | 'sold';
export type ParcelType   = 'residentiel' | 'commercial' | 'agricole' | 'industriel';

export interface Parcel {
  id:               string;
  titre:            string;
  localisation:     string;
  region:           string;
  superficie:       number;
  price:            number;
  type_terrain:     ParcelType;
  status:           ParcelStatus;
  owner_id:         string;
  vendeur_nom?:     string;
  document_hash?:   string;
  blockchain_tx_hash?: string;
  ipfs_hash?:       string;
  created_at:       string;
  certified_at?:    string;
  location?: {
    latitude:  number;
    longitude: number;
  };
}

export interface ParcelDetail extends Parcel {
  description:      string;
  photos:           { id: string; url: string; is_primary: boolean }[];
  certificat?: {
    hash_blockchain:  string;
    date_validation:  string;
    adresse_contrat?: string;
  };
}

// ─── Transaction ───
export type TxStatus = 'initie' | 'en_cours' | 'complete' | 'annulee';

export interface Transaction {
  id:           string;
  parcel_id:    string;
  parcel_titre: string;
  acheteur_nom: string;
  vendeur_nom:  string;
  montant:      number;
  status:       TxStatus;
  created_at:   string;
}

// ─── Audit ───
export interface AuditLog {
  id:         string;
  user_id:    string;
  action:     string;
  ip_address: string;
  metadata:   Record<string, unknown>;
  created_at: string;
}

// ─── Dashboard Stats ───
export interface DashboardStats {
  users: {
    total:        number;
    pending_kyc:  number;
    new_today:    number;
  };
  parcels: {
    total:        number;
    pending:      number;
    certified:    number;
    rejected:     number;
  };
  transactions: {
    total:        number;
    completed:    number;
    volume_fcfa:  number;
  };
  blockchain: {
    total_tx:     number;
    last_block:   number;
  };
}

// ─── API generics ───
export interface PaginatedResponse<T> {
  count:    number;
  page:     number;
  results:  T[];
}

export interface ApiError {
  error: {
    code:     string;
    message:  string;
    details?: Record<string, string[]>;
  };
}

export interface ValidationDecision {
  decision: 'approve' | 'reject';
  reason?:  string;
}
