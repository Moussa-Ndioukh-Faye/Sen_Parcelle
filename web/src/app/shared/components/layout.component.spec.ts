import { TestBed } from '@angular/core/testing';
import { LayoutComponent } from './layout/layout.component';
import { provideRouter } from '@angular/router';
import { AuthService } from '@core/services/auth.service';

describe('LayoutComponent', () => {
  let authSpy: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    authSpy = jasmine.createSpyObj('AuthService', [
      'user', 'isAdmin', 'logout', 'userInitials',
    ]);
    authSpy.user.and.returnValue(null);

    await TestBed.configureTestingModule({
      imports: [LayoutComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authSpy },
      ],
    }).compileComponents();
  });

  it('devrait être créé', () => {
    const fixture = TestBed.createComponent(LayoutComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('devrait afficher la sidebar', () => {
    const fixture = TestBed.createComponent(LayoutComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('aside')).toBeTruthy();
  });

  it('logout doit déconnecter', () => {
    const fixture = TestBed.createComponent(LayoutComponent);
    const component = fixture.componentInstance;
    component.auth.logout();
    expect(authSpy.logout).toHaveBeenCalled();
  });
});
