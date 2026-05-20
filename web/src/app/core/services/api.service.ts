import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '@env/environment';
import { ApiError } from '../models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  private _globalLoading = signal(0);
  readonly isLoading = computed(() => this._globalLoading() > 0);

  private getHeaders(auth = true): HttpHeaders {
    let headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    if (auth) {
      const token = localStorage.getItem('access_token');
      if (token) headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  get<T>(path: string, params: Record<string, string | number | boolean> = {}, auth = true): Observable<T> {
    let httpParams = new HttpParams();
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        httpParams = httpParams.set(key, String(params[key]));
      }
    });

    this._globalLoading.update(n => n + 1);
    return this.http.get<T>(`${this.baseUrl}${path}`, {
      headers: this.getHeaders(auth),
      params: httpParams
    }).pipe(
      tap(() => this._globalLoading.update(n => n - 1)),
      catchError((err: unknown) => {
        this._globalLoading.update(n => n - 1);
        return this.handleError(err as HttpErrorResponse);
      })
    );
  }

  post<T>(path: string, body: any, auth = true): Observable<T> {
    this._globalLoading.update(n => n + 1);
    return this.http.post<T>(`${this.baseUrl}${path}`, body, {
      headers: this.getHeaders(auth)
    }).pipe(
      tap(() => this._globalLoading.update(n => n - 1)),
      catchError((err: unknown) => {
        this._globalLoading.update(n => n - 1);
        return this.handleError(err as HttpErrorResponse);
      })
    );
  }

  put<T>(path: string, body: any): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${path}`, body, {
      headers: this.getHeaders()
    }).pipe(catchError((err: unknown) => this.handleError(err as HttpErrorResponse)));
  }

  patch<T>(path: string, body: any): Observable<T> {
    return this.http.patch<T>(`${this.baseUrl}${path}`, body, {
      headers: this.getHeaders()
    }).pipe(catchError((err: unknown) => this.handleError(err as HttpErrorResponse)));
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${path}`, {
      headers: this.getHeaders()
    }).pipe(catchError((err: unknown) => this.handleError(err as HttpErrorResponse)));
  }

  private handleError(err: HttpErrorResponse): Observable<never> {
    const apiError = err.error as ApiError;
    const message = apiError?.error?.message ?? err.message ?? 'Erreur inconnue';
    return throwError(() => ({
      status: err.status,
      code: apiError?.error?.code ?? 'unknown',
      message,
      details: apiError?.error?.details
    }));
  }
}
