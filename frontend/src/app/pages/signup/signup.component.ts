import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-brand">
          <div class="auth-brand-icon">🧠</div>
          <span class="auth-brand-name">Production RAG System</span>
        </div>
        <div class="auth-h">Create account</div>
        <div class="auth-sub">Start analyzing documents intelligently</div>
        <div class="fgrp">
          <label class="flbl">Full Name</label>
          <input type="text" class="finp" [(ngModel)]="name" placeholder="John Doe" />
        </div>
        <div class="fgrp">
          <label class="flbl">Email Address</label>
          <input type="email" class="finp" [(ngModel)]="email" placeholder="you@example.com" />
        </div>
        <div class="fgrp">
          <label class="flbl">Password</label>
          <div class="password-input-wrap">
            <input [type]="showPassword ? 'text' : 'password'" class="finp" [(ngModel)]="password" placeholder="Min. 8 characters" />
            <button type="button" class="pwd-toggle" (click)="showPassword = !showPassword" title="Toggle password visibility">
              {{ showPassword ? '🔒' : '👁' }}
            </button>
          </div>
        </div>
        <style>
          .password-input-wrap { position: relative; }
          .pwd-toggle { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 18px; opacity: 0.7; transition: opacity 0.2s; }
          .pwd-toggle:hover { opacity: 1; }
        </style>
        <button class="btn btn-primary" (click)="doSignup()" [disabled]="loading">
          {{ loading ? 'Creating…' : 'Create Account →' }}
        </button>
        <div class="auth-switch">Already have an account? <a (click)="router.navigate(['/login'])">Sign in</a></div>
      </div>
    </div>
  `
})
export class SignupComponent {
  auth   = inject(AuthService);
  toast  = inject(ToastService);
  router = inject(Router);

  name = ''; email = ''; password = ''; loading = false; showPassword = false;

  doSignup(): void {
    if (!this.name || !this.email || !this.password) { this.toast.show('Please fill all fields', 'err'); return; }
    this.loading = true;
    this.auth.signup(this.name, this.email, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/otp'], { state: { email: this.email, type: 'EMAIL_VERIFY' } });
        this.toast.show('OTP sent! Check your email.', 'ok');
      },
      error: err => { this.loading = false; this.toast.show(err.error?.detail || 'Signup failed', 'err'); }
    });
  }
}
