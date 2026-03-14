import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-forgot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-brand">
          <div class="auth-brand-icon">🔑</div>
          <span class="auth-brand-name">Reset Password</span>
        </div>
        <div class="auth-h">Forgot password?</div>
        <div class="auth-sub">Enter your email and we'll send a reset OTP</div>
        <div class="fgrp">
          <label class="flbl">Email Address</label>
          <input type="email" class="finp" [(ngModel)]="email" placeholder="you@example.com" (keydown.enter)="doForgot()" />
        </div>
        <button class="btn btn-primary" (click)="doForgot()" [disabled]="loading">
          {{ loading ? 'Sending…' : 'Send Reset OTP →' }}
        </button>
        <div class="auth-switch"><a (click)="router.navigate(['/login'])">← Back to login</a></div>
      </div>
    </div>
  `
})
export class ForgotComponent {
  auth   = inject(AuthService);
  toast  = inject(ToastService);
  router = inject(Router);

  email = ''; loading = false;

  doForgot(): void {
    if (!this.email) { this.toast.show('Enter your email', 'err'); return; }
    this.loading = true;
    this.auth.sendResetOtp(this.email).subscribe({
      next: () => {
        this.loading = false;
        this.toast.show('Reset OTP sent!', 'ok');
        this.router.navigate(['/reset'], { state: { email: this.email } });
      },
      error: err => { this.loading = false; this.toast.show(err.error?.detail || 'Failed', 'err'); }
    });
  }
}
