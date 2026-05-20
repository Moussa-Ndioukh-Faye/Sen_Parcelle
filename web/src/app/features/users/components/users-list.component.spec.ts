import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { UsersListComponent } from './users-list.component';

describe('UsersListComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    localStorage.setItem('access_token', 'mock_token');
    await TestBed.configureTestingModule({
      imports: [UsersListComponent, HttpClientTestingModule],
      providers: [provideRouter([])],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être créé', () => {
    const fixture = TestBed.createComponent(UsersListComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });
});
