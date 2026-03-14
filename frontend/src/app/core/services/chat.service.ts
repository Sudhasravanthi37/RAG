import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Chat, Message, SendMessageResponse, UploadResponse } from '../models/models';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private api = environment.apiUrl;

  chats        = signal<Chat[]>([]);
  currentChat  = signal<Chat | null>(null);
  messages     = signal<Message[]>([]);
  isTyping     = signal(false);
  currentMode  = signal('qa');
  incognito    = signal(false);
  incognitoSid = signal<string | null>(null);

  constructor(private http: HttpClient) {}

  // GET /chats
  loadChats(): Observable<Chat[]> {
    return this.http.get<Chat[]>(`${this.api}/chats`).pipe(
      tap(chats => this.chats.set(chats))
    );
  }

  // POST /chat/new
  createChat(title = 'New Chat', mode = 'qa'): Observable<{ chat_id: string; title: string }> {
    return this.http.post<{ chat_id: string; title: string }>(`${this.api}/chat/new`, { title, mode }).pipe(
      tap(res => {
        const newChat: Chat = { chat_id: res.chat_id, title: res.title, created_at: new Date().toISOString(), last_message_at: null };
        this.chats.update(c => [newChat, ...c]);
        this.openChat(newChat);
      })
    );
  }

  // GET /chats/:id/messages
  loadMessages(chatId: string): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.api}/chats/${chatId}/messages`).pipe(
      tap(msgs => this.messages.set(msgs))
    );
  }

  openChat(chat: Chat): void {
    this.currentChat.set(chat);
    this.messages.set([]);
    this.loadMessages(chat.chat_id).subscribe();
  }

  // DELETE /chats/:id
  deleteChat(chatId: string): Observable<any> {
    return this.http.delete(`${this.api}/chats/${chatId}`).pipe(
      tap(() => {
        this.chats.update(c => c.filter(x => x.chat_id !== chatId));
        if (this.currentChat()?.chat_id === chatId) {
          this.currentChat.set(null);
          this.messages.set([]);
        }
      })
    );
  }

  // POST /chat
  sendMessage(payload: {
    chat_id: string; mode: string; query: string;
    incognito: boolean; incognito_session_id: string;
  }): Observable<SendMessageResponse> {
    this.isTyping.set(true);
    return this.http.post<SendMessageResponse>(`${this.api}/chat`, payload).pipe(
      tap({
        next: () => this.isTyping.set(false),
        error: () => this.isTyping.set(false),
      })
    );
  }

  // POST /upload
  uploadFile(file: File, chatId: string): Observable<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    form.append('chat_id', chatId);
    form.append('incognito', String(this.incognito()));
    return this.http.post<UploadResponse>(`${this.api}/upload`, form);
  }

  toggleIncognito(): void {
    this.incognito.update(v => !v);
    if (!this.incognito()) this.incognitoSid.set(null);
  }

  updateChatTitle(chatId: string, title: string): void {
    this.chats.update(list =>
      list.map(c => c.chat_id === chatId ? { ...c, title } : c)
    );
    if (this.currentChat()?.chat_id === chatId) {
      this.currentChat.update(c => c ? { ...c, title } : c);
    }
  }
}
