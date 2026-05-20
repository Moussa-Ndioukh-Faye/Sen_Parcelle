import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { ParcelDetailComponent } from './parcel-detail.component';

describe('ParcelDetailComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    localStorage.setItem('access_token', 'mock_token');
    await TestBed.configureTestingModule({
      imports: [ParcelDetailComponent, HttpClientTestingModule],
      providers: [provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    const fixture = TestBed.createComponent(ParcelDetailComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });
});
