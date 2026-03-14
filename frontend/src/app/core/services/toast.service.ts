import { Injectable, signal } from '@angular/core';
import { Toast } from '../models/models';

@Injectable({ providedIn: 'root' })
export class ToastService {
  toasts = signal<Toast[]>([]);
  private id = 0;

  show(message: string, type: '' | 'ok' | 'err' | 'warn' = ''): void {
    const toast: Toast = { id: ++this.id, message, type };
    this.toasts.update(t => [...t, toast]);
    setTimeout(() => this.toasts.update(t => t.filter(x => x.id !== toast.id)), 3600);
  }
}
