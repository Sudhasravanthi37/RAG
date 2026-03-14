import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-reset',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-brand">
          <div class="auth-brand-icon">🔑</div>
          <span class="auth-brand-name">New Password</span>
        </div>
        <div class="auth-h">Set new password</div>
        <div class="auth-sub">Enter the OTP sent to {{ email }} and your new password</div>
        <div class="otp-row">
          @for (i of [0,1,2,3,4,5]; track i) {
            <input class="otp-box" maxlength="1" type="text" inputmode="numeric"
              [(ngModel)]="digits[i]"
              (input)="onInput(i)"
              (keydown)="onKeydown($event, i)" />
          }
        </div>
        <div class="fgrp">
          <label class="flbl">New Password</label>
          <input type="password" class="finp" [(ngModel)]="newPwd" placeholder="Enter new password" />
        </div>
        <button class="btn btn-primary" (click)="doReset()" [disabled]="loading">
          {{ loading ? 'Resetting…' : 'Reset Password →' }}
        </button>
      </div>
    </div>
  `
})
export class ResetComponent implements OnInit {
  auth   = inject(AuthService);
  toast  = inject(ToastService);
  router = inject(Router);

  email   = '';
  digits  = ['', '', '', '', '', ''];
  newPwd  = '';
  loading = false;

  ngOnInit(): void {
    this.email = history.state?.email || '';
    if (!this.email) this.router.navigate(['/forgot']);
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

  doReset(): void {
    const otp = this.digits.join('');
    if (otp.length !== 6 || !this.newPwd) { this.toast.show('Fill all fields', 'err'); return; }
    this.loading = true;
    this.auth.resetPasswordConfirm(this.email, otp, this.newPwd).subscribe({
      next: () => {
        this.loading = false;
        this.toast.show('Password reset! Please log in.', 'ok');
        this.router.navigate(['/login']);
      },
      error: err => { this.loading = false; this.toast.show(err.error?.detail || 'Failed', 'err'); }
    });
  }
}
