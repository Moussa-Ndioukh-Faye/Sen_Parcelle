import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { BlockchainComponent } from './blockchain.component';
import { provideRouter } from '@angular/router';

describe('BlockchainComponent', () => {
  beforeEach(async () => {
    localStorage.setItem('access_token', 'mock_token');
    await TestBed.configureTestingModule({
      imports: [BlockchainComponent, HttpClientTestingModule],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  afterEach(() => localStorage.clear());

  it('devrait être créé', () => {
    const fixture = TestBed.createComponent(BlockchainComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('devrait avoir le titre Blockchain', () => {
    const fixture = TestBed.createComponent(BlockchainComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Polygon');
  });

  it('devrait afficher le vérificateur', () => {
    const fixture = TestBed.createComponent(BlockchainComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('input')).toBeTruthy();
    expect(compiled.querySelector('button')).toBeTruthy();
  });

  it('getExplorerUrl doit retourner le bon liens', () => {
    const fixture = TestBed.createComponent(BlockchainComponent);
    const component = fixture.componentInstance;
    expect(component.getExplorerUrl('0xabc')).toBe('https://polygonscan.com/tx/0xabc');
    expect(component.getExplorerUrl()).toBe('#');
  });
});
