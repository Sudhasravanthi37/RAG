import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login',    canActivate: [guestGuard], loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  { path: 'signup',   canActivate: [guestGuard], loadComponent: () => import('./pages/signup/signup.component').then(m => m.SignupComponent) },
  { path: 'otp',      loadComponent: () => import('./pages/otp/otp.component').then(m => m.OtpComponent) },
  { path: 'forgot',   canActivate: [guestGuard], loadComponent: () => import('./pages/forgot/forgot.component').then(m => m.ForgotComponent) },
  { path: 'reset',    loadComponent: () => import('./pages/reset/reset.component').then(m => m.ResetComponent) },
  { path: 'app',      canActivate: [authGuard],  loadComponent: () => import('./pages/app-shell/app-shell.component').then(m => m.AppShellComponent) },
  { path: '**', redirectTo: 'login' }
];
