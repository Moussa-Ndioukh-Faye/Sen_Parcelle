import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BlockchainService } from './blockchain.service';

describe('BlockchainService', () => {
  let service: BlockchainService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [BlockchainService],
    });
    service = TestBed.inject(BlockchainService);
    httpMock = TestBed.inject(HttpTestingController);
    localStorage.setItem('access_token', 'mock_token');
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    expect(service).toBeTruthy();
  });

  it('getInfo doit retourner les infos blockchain', (done) => {
    service.getInfo().subscribe((info) => {
      expect(info.chainId).toBe(80001);
      expect(info.contractAddress).toBe('0x1234...');
      done();
    });

    const req = httpMock.expectOne((r) =>
      r.url.endsWith('/blockchain/info/')
    );
    expect(req.request.method).toBe('GET');
    req.flush({
      chainId: 80001,
      contractAddress: '0x1234...',
      lastBlock: 42000,
      totalParcels: 85,
      network: 'Mumbai',
    });
  });

  it('verifyDocument doit vérifier un hash', (done) => {
    service.verifyDocument('hash123').subscribe((result) => {
      expect(result.verified).toBe(true);
      expect(result.timestamp).toBeTruthy();
      done();
    });

    const req = httpMock.expectOne((r) =>
      r.url.includes('/blockchain/verify/')
    );
    req.flush({
      verified: true,
      timestamp: '2026-05-10T12:00:00Z',
      blockNumber: 42001,
    });
  });

  it('getContractBalance doit retourner le solde', (done) => {
    service.getContractBalance().subscribe((balance) => {
      expect(balance.wei).toBe('1000000000000000000');
      expect(balance.eth).toBe('1.0');
      done();
    });

    const req = httpMock.expectOne((r) =>
      r.url.includes('/blockchain/balance/')
    );
    req.flush({ wei: '1000000000000000000', eth: '1.0' });
  });
});
