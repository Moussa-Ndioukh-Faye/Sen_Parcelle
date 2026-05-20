import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { ParcelsListComponent } from './parcels-list.component';

describe('ParcelsListComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    localStorage.setItem('access_token', 'mock_token');
    await TestBed.configureTestingModule({
      imports: [ParcelsListComponent, HttpClientTestingModule],
      providers: [provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    const fixture = TestBed.createComponent(ParcelsListComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('devrait charger les parcelles', () => {
    const fixture = TestBed.createComponent(ParcelsListComponent);
    fixture.detectChanges();
    const req = httpMock.expectOne(r => r.url.includes('/parcelles/'));
    req.flush({ count: 0, results: [] });
    expect(fixture.componentInstance).toBeTruthy();
  });
});
