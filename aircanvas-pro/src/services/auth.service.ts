import { Injectable, signal, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, map, of, tap, throwError } from 'rxjs';

export interface AuthUser {
  id?: string;
  name: string;
  email: string;
  is_admin?: boolean;
  role?: 'ADMIN' | 'USER';
  theme?: string;
  mode?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    email: string;
    is_admin: boolean;
  };
}

interface MeResponse {
  id: string;
  name: string;
  email: string;
  is_admin: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  isAuthenticated = signal<boolean>(false);
  isAdmin = signal<boolean>(false);
  user = signal<AuthUser | null>(null);

  private http = inject(HttpClient);

  private readonly USER_KEY = 'aircanvas_user';
  private readonly TOKEN_KEY = 'aircanvas_user_token';
  private readonly API_BASE_URL_KEY = 'aircanvas_api_base_url';
  private readonly API_PREFIX = '/api/v1';
  private readonly apiBase = this.resolveApiBase();

  constructor() {
    this.bootstrapFromStorage();
  }

  login(email: string, password: string): Observable<AuthUser> {
    return this.http
      .post<AuthResponse>(`${this.apiBase}${this.API_PREFIX}/auth/login`, { email, password })
      .pipe(
        map((payload) => this.persistAuth(payload)),
        catchError((error) => throwError(() => new Error(this.errorMessage(error))))
      );
  }

  signup(
    name: string,
    email: string,
    password: string,
  ): Observable<AuthUser> {
    return this.http
      .post<AuthResponse>(`${this.apiBase}${this.API_PREFIX}/auth/register`, {
        name,
        email,
        password,
      })
      .pipe(
        map((payload) => this.persistAuth(payload)),
        catchError((error) => throwError(() => new Error(this.errorMessage(error))))
      );
  }

  refreshProfile(): Observable<AuthUser | null> {
    const token = this.getToken();
    if (!token) {
      return of(null);
    }

    return this.http
      .get<MeResponse>(`${this.apiBase}${this.API_PREFIX}/auth/me`, {
        headers: new HttpHeaders(this.authHeaders(false)),
      })
      .pipe(
        tap((me) => {
          const existing = this.user();
          const nextUser: AuthUser = {
            ...existing,
            id: me.id,
            name: me.name,
            email: me.email,
            is_admin: me.is_admin,
            role: me.is_admin ? 'ADMIN' : 'USER',
          };
          this.setAuthState(nextUser);
        }),
        map(() => this.user()),
        catchError((error) => {
          this.logout();
          return throwError(() => new Error(this.errorMessage(error)));
        }),
      );
  }

  logout() {
    this.isAuthenticated.set(false);
    this.isAdmin.set(false);
    this.user.set(null);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.TOKEN_KEY);
  }

  updateProfile(data: { theme: string; mode: string }) {
    this.user.update((u) => (u ? { ...u, ...data } : null));
    const current = this.user();
    if (current) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(current));
    }
  }

  apiBaseUrl(): string {
    return this.apiBase;
  }

  apiPrefix(): string {
    return this.API_PREFIX;
  }

  getToken(): string {
    return localStorage.getItem(this.TOKEN_KEY)?.trim() || '';
  }

  authHeaders(includeContentType: boolean = true): Record<string, string> {
    const headers: Record<string, string> = {};
    const token = this.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (includeContentType) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  pythonEnvHint(): string {
    const token = this.getToken() || '<paste-jwt-from-login>';
    return [
      `API_BASE_URL=${this.apiBase}`,
      `AIRCANVAS_API_BASE_URL=${this.apiBase}`,
      `AIRCANVAS_JWT_TOKEN=${token}`,
    ].join('\n');
  }

  private bootstrapFromStorage(): void {
    const rawUser = localStorage.getItem(this.USER_KEY);
    const token = this.getToken();
    if (!rawUser || !token) {
      this.logout();
      return;
    }

    try {
      const storedUser = JSON.parse(rawUser) as AuthUser;
      this.setAuthState(storedUser);
    } catch {
      this.logout();
      return;
    }

    this.refreshProfile().subscribe({
      error: () => {
        // refreshProfile already clears auth on failure
      },
    });
  }

  private persistAuth(payload: AuthResponse): AuthUser {
    const nextUser: AuthUser = {
      id: payload.user.id,
      name: payload.user.name,
      email: payload.user.email,
      is_admin: payload.user.is_admin,
      role: payload.user.is_admin ? 'ADMIN' : 'USER',
    };
    localStorage.setItem(this.TOKEN_KEY, payload.access_token);
    this.setAuthState(nextUser);
    return nextUser;
  }

  private setAuthState(user: AuthUser): void {
    this.user.set(user);
    this.isAuthenticated.set(true);
    this.isAdmin.set(Boolean(user.is_admin) || user.role === 'ADMIN');
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  private resolveApiBase(): string {
    const stored = localStorage.getItem(this.API_BASE_URL_KEY)?.trim();
    if (stored) {
      return stored.replace(/\/+$/, '');
    }

    const origin = window.location.origin.replace(/\/+$/, '');
    if (!origin) {
      return 'http://127.0.0.1:8000';
    }

    try {
      const url = new URL(origin);
      const host = url.hostname.toLowerCase();
      const port = url.port;
      const isLocalHost = host === 'localhost' || host === '127.0.0.1' || host === '::1';
      const devPorts = new Set(['3000', '4200', '5173']);

      // Angular/Vite dev servers should call FastAPI on 8000, not self-origin.
      if (isLocalHost && devPorts.has(port)) {
        return 'http://127.0.0.1:8000';
      }
      return origin;
    } catch {
      return 'http://127.0.0.1:8000';
    }
  }

  private errorMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const payload = error.error;
      if (typeof payload === 'string' && payload.trim()) {
        return payload;
      }
      if (payload && typeof payload.detail === 'string') {
        return payload.detail;
      }
      if (error.status) {
        return `Request failed (${error.status})`;
      }
      return 'Unable to reach backend API.';
    }
    if (error instanceof Error) {
      return error.message;
    }
    return 'Unknown error';
  }
}
