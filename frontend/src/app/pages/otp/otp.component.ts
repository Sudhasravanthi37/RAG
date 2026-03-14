import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-otp',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-brand">
          <div class="auth-brand-icon">✉️</div>
          <span class="auth-brand-name">Verify Email</span>
        </div>
        <div class="auth-h">Check your inbox</div>
        <div class="auth-sub">We sent a 6-digit code to {{ email }}</div>
        <div class="otp-row">
          @for (i of [0,1,2,3,4,5]; track i) {
            <input #otpBoxes class="otp-box" maxlength="1" type="text" inputmode="numeric"
              [(ngModel)]="digits[i]"
              (input)="onInput(i)"
              (keydown)="onKeydown($event, i)" />
          }
        </div>
        <button class="btn btn-primary" (click)="doVerify()" [disabled]="loading">
          {{ loading ? 'Verifying…' : 'Verify →' }}
        </button>
        <div class="auth-switch">
          <a (click)="router.navigate(['/login'])">← Back to login</a>
          &nbsp;&nbsp;
          <a (click)="doResend()">Resend OTP</a>
        </div>
      </div>
    </div>
  `
})
export class OtpComponent implements OnInit {
  auth   = inject(AuthService);
  toast  = inject(ToastService);
  router = inject(Router);

  email   = '';
  otpType = 'EMAIL_VERIFY';
  digits  = ['', '', '', '', '', ''];
  loading = false;

  ngOnInit(): void {
    const state = history.state;
    this.email   = state?.email || '';
    this.otpType = state?.type  || 'EMAIL_VERIFY';
    if (!this.email) this.router.navigate(['/login']);
  }

  onInput(i: number): void {
    const boxes = document.querySelectorAll<HTMLInputElement>('.otp-box');
    if (this.digits[i] && i < 5) boxes[i + 1]?.focus();
  }

  onKeydown(e: KeyboardEvent, i: number): void {
    if (e.key === 'Backspace' && !this.digits[i] && i > 0) {
      const boxes = document.querySelectorAll<HTMLInputElement>('.otp-box');
      boxes[i - 1]?.focus();
    }
  }

  doVerify(): void {
    const otp = this.digits.join('');
    if (otp.length !== 6) { this.toast.show('Enter all 6 digits', 'err'); return; }
    this.loading = true;
    this.auth.verifyOtp(this.email, otp, this.otpType).subscribe({
      next: () => {
        this.loading = false;
        this.toast.show('Email verified! Please log in.', 'ok');
        this.router.navigate(['/login']);
      },
      error: err => { this.loading = false; this.toast.show(err.error?.detail || 'OTP failed', 'err'); }
    });
  }

  doResend(): void {
    this.auth.resendOtp(this.email).subscribe({
      next: (r: any) => this.toast.show(r.message || 'OTP resent', 'ok'),
      error: () => this.toast.show('Failed to resend', 'err')
    });
  }
}
