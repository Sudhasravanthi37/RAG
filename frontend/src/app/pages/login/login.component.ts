import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-brand">
          <div class="auth-brand-icon">🧠</div>
          <span class="auth-brand-name">Production RAG System</span>
        </div>
        <div class="auth-h">Welcome back</div>
        <div class="auth-sub">Sign in to your account to continue</div>
        <div class="fgrp">
          <label class="flbl">Email Address</label>
          <input type="email" class="finp" [(ngModel)]="email" placeholder="you@example.com" (keydown.enter)="doLogin()" />
        </div>
        <div class="fgrp">
          <label class="flbl">Password</label>
          <input type="password" class="finp" [(ngModel)]="password" placeholder="••••••••" (keydown.enter)="doLogin()" />
        </div>
        <div style="text-align:right;margin-bottom:18px;margin-top:-8px;">
          <button class="auth-link" (click)="router.navigate(['/forgot'])">Forgot password?</button>
        </div>
        <button class="btn btn-primary" (click)="doLogin()" [disabled]="loading">
          {{ loading ? 'Signing in…' : 'Sign In →' }}
        </button>
        <div class="auth-switch">No account? <a (click)="router.navigate(['/signup'])">Create one</a></div>
      </div>
    </div>
  `
})
export class LoginComponent {
  auth   = inject(AuthService);
  toast  = inject(ToastService);
  router = inject(Router);

  email    = '';
  password = '';
  loading  = false;

  doLogin(): void {
    if (!this.email || !this.password) { this.toast.show('Please fill all fields', 'err'); return; }
    this.loading = true;
    this.auth.login(this.email, this.password).subscribe({
      next: () => {
        this.auth.fetchProfile().subscribe({
          next: () => { this.router.navigate(['/app']); this.toast.show('Welcome back! 👋', 'ok'); },
          error: () => { this.router.navigate(['/app']); }
        });
      },
      error: err => {
        this.loading = false;
        this.toast.show(err.error?.detail || 'Login failed', 'err');
      }
    });
  }
}
