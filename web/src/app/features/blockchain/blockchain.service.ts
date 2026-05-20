import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '@core/services/api.service';

export interface BlockchainInfo {
  chainId: number;
  contractAddress: string;
  lastBlock: number;
  totalParcels: number;
  network: string;
}

export interface VerifyResult {
  verified: boolean;
  timestamp?: string;
  blockNumber?: number;
  parcelle?: string;
  date_validation?: string;
}

export interface ContractBalance {
  wei: string;
  eth: string;
}

@Injectable({ providedIn: 'root' })
export class BlockchainService {
  private readonly api = inject(ApiService);

  getInfo(): Observable<BlockchainInfo> {
    return this.api.get<BlockchainInfo>('/blockchain/info/');
  }

  verifyDocument(hash: string): Observable<VerifyResult> {
    return this.api.get<VerifyResult>(`/blockchain/verify/${hash}/`);
  }

  getContractBalance(): Observable<ContractBalance> {
    return this.api.get<ContractBalance>('/blockchain/balance/');
  }
}
