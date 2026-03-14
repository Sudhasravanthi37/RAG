import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User } from '../models/models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = environment.apiUrl;

  currentUser = signal<User | null>(
    JSON.parse(localStorage.getItem('rg_user') || 'null')
  );
  token = signal<string | null>(localStorage.getItem('rg_tk'));

  constructor(private http: HttpClient, private router: Router) {}

  // POST /auth/login
  login(email: string, password: string): Observable<{ access_token: string }> {
    return this.http.post<{ access_token: string }>(`${this.api}/auth/login`, { email, password }).pipe(
      tap(res => {
        this.token.set(res.access_token);
        localStorage.setItem('rg_tk', res.access_token);
      })
    );
  }

  // POST /auth/signup
  signup(name: string, email: string, password: string): Observable<any> {
    return this.http.post(`${this.api}/auth/signup`, { name, email, password });
  }

  // POST /auth/verify-otp
  verifyOtp(email: string, otp: string, otp_type: string): Observable<any> {
    return this.http.post(`${this.api}/auth/verify-otp`, { email, otp, otp_type });
  }

  // POST /auth/confirm-email (resend OTP)
  resendOtp(email: string): Observable<any> {
    return this.http.post(`${this.api}/auth/confirm-email`, { email });
  }

  // POST /auth/reset-password (send reset OTP)
  sendResetOtp(email: string): Observable<any> {
    return this.http.post(`${this.api}/auth/reset-password`, { email });
  }

  // POST /auth/reset-password/confirm
  resetPasswordConfirm(email: string, otp: string, new_password: string): Observable<any> {
    return this.http.post(`${this.api}/auth/reset-password/confirm`, { email, otp, new_password });
  }

  // GET /auth/profile
  fetchProfile(): Observable<User> {
    return this.http.get<User>(`${this.api}/auth/profile`).pipe(
      tap(user => {
        this.currentUser.set(user);
        localStorage.setItem('rg_user', JSON.stringify(user));
      })
    );
  }

  // POST /auth/logout
  logout(): void {
    this.http.post(`${this.api}/auth/logout`, {}).subscribe();
    this.token.set(null);
    this.currentUser.set(null);
    localStorage.removeItem('rg_tk');
    localStorage.removeItem('rg_user');
    this.router.navigate(['/login']);
  }

  // PATCH /profile/username
  changeUsername(new_name: string): Observable<any> {
    return this.http.patch(`${this.api}/profile/username`, { new_name }).pipe(
      tap(() => this.fetchProfile().subscribe())
    );
  }

  // PATCH /profile/password
  changePassword(current_password: string, new_password: string): Observable<any> {
    return this.http.patch(`${this.api}/profile/password`, { current_password, new_password });
  }

  // POST /profile/picture
  uploadProfilePic(file: File): Observable<any> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post(`${this.api}/profile/picture`, form).pipe(
      tap(() => this.fetchProfile().subscribe())
    );
  }

  isLoggedIn(): boolean {
    return !!this.token();
  }

  get userInitial(): string {
    return (this.currentUser()?.name || 'U')[0].toUpperCase();
  }
}
