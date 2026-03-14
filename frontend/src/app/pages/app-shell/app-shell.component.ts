import {
  Component, inject, OnInit, ViewChild, ElementRef,
  AfterViewChecked, HostListener, signal
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { AuthService } from '../../core/services/auth.service';
import { ChatService } from '../../core/services/chat.service';
import { ToastService } from '../../core/services/toast.service';
import { environment } from '../../../environments/environment';
import { Message, RetrievalMetrics } from '../../core/models/models';

interface FileChip { id: number; name: string; status: string; done: boolean; error: boolean; }
interface UploadedFile { id: string; name: string; chunks: number; uploadedAt: string; }

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
<!-- ══ TOP BAR ══════════════════════════════════════════════════════════ -->
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-brand-icon">🧠</div>
    <span class="topbar-brand-name">Production RAG System</span>
  </div>
  <div class="topbar-spacer"></div>
  <div class="topbar-nav">
    <button class="topbar-nav-link" (click)="openDocs()">Docs</button>
    <button class="topbar-nav-link">About</button>
    <button class="topbar-nav-link" (click)="openApi()">API</button>
  </div>
  @if (chatSvc.incognito()) {
    <div class="incognito-pill">🕵️ Incognito</div>
  }
  <div class="avatar-wrap">
    <button class="avatar-btn" id="av-btn" (click)="toggleProfile($event)">
      @if (authSvc.currentUser()?.profile_pic_url) {
        <img [src]="apiUrl + authSvc.currentUser()!.profile_pic_url" alt="avatar">
      } @else {
        <span>{{ authSvc.userInitial }}</span>
      }
    </button>
  </div>
</div>

<!-- ══ PROFILE PANEL ════════════════════════════════════════════════════ -->
@if (showProfile) {
  <div class="overlay" (click)="closeProfile($event)">
    <div class="profile-panel" (click)="$event.stopPropagation()">
      <div class="pp-head">
        <div class="pp-avatar" (click)="picInput.click()">
          @if (authSvc.currentUser()?.profile_pic_url) {
            <img [src]="apiUrl + authSvc.currentUser()!.profile_pic_url" alt="avatar">
          } @else {
            <span>{{ authSvc.userInitial }}</span>
          }
        </div>
        <div class="pp-name">{{ authSvc.currentUser()?.name }}</div>
        <div class="pp-email">{{ authSvc.currentUser()?.email }}</div>
      </div>
      <div class="pp-menu">
        <button class="pp-item" (click)="openModal('username')">🔤&nbsp; Change Username</button>
        <button class="pp-item" (click)="openModal('password')">🔒&nbsp; Change Password</button>
        <button class="pp-item" (click)="picInput.click()">🖼️&nbsp; Change Profile Picture</button>
        <div class="pp-divider"></div>
        <button class="pp-item red" (click)="authSvc.logout()">🚪&nbsp; Sign Out</button>
      </div>
    </div>
  </div>
  <input #picInput type="file" style="display:none" accept=".jpg,.jpeg,.png,.webp" (change)="uploadPic($event)">
}

<!-- ══ MODALS ════════════════════════════════════════════════════════════ -->
@if (activeModal === 'username') {
  <div class="modal-wrap" (click)="closeModal()">
    <div class="modal" (click)="$event.stopPropagation()">
      <div class="modal-title">🔤 Change Username</div>
      <div class="fgrp">
        <label class="flbl">New Username</label>
        <input type="text" class="finp" [(ngModel)]="newUsername" placeholder="Enter new username" />
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" (click)="closeModal()">Cancel</button>
        <button class="btn btn-primary" (click)="saveUsername()">Save</button>
      </div>
    </div>
  </div>
}
@if (activeModal === 'password') {
  <div class="modal-wrap" (click)="closeModal()">
    <div class="modal" (click)="$event.stopPropagation()">
      <div class="modal-title">🔒 Change Password</div>
      <div class="fgrp">
        <label class="flbl">Current Password</label>
        <input type="password" class="finp" [(ngModel)]="curPwd" placeholder="••••••••" />
      </div>
      <div class="fgrp">
        <label class="flbl">New Password</label>
        <input type="password" class="finp" [(ngModel)]="newPwd" placeholder="Min. 8 characters" />
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" (click)="closeModal()">Cancel</button>
        <button class="btn btn-primary" (click)="savePassword()">Change Password</button>
      </div>
    </div>
  </div>
}

<!-- ══ APP SHELL ═════════════════════════════════════════════════════════ -->
<div class="app">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-top">
      <button class="new-chat-btn" (click)="createChat()">
        <span style="font-size:20px;line-height:1">＋</span> New Chat
      </button>
    </div>
    <div class="sidebar-section">Chat History</div>
    <div class="sidebar-list">
      @if (!chatSvc.chats().length) {
        <div class="sidebar-empty">No chats yet — create one!</div>
      }
      @for (c of chatSvc.chats(); track c.chat_id) {
        <div class="chat-row" [class.active]="chatSvc.currentChat()?.chat_id === c.chat_id"
             (click)="chatSvc.openChat(c)">
          <div class="chat-row-icon" [style.background]="chatColor(c.chat_id)">📄</div>
          <div class="chat-row-body">
            <div class="chat-row-title">{{ c.title || 'New Chat' }}</div>
            <div class="chat-row-time">{{ timeAgo(c.last_message_at || c.created_at) }}</div>
          </div>
          <button class="chat-row-del" title="Delete chat" (click)="delChat($event, c.chat_id)"></button>
        </div>
      }
    </div>
  </div>

  <!-- MAIN -->
  <div class="main">

    <!-- HERO -->
    <div class="hero">
      <div class="hero-left">
        <div class="hero-title">🧠 Intelligent Document Understanding System</div>
      </div>
      <div class="hero-divider"></div>
      <div class="hero-right">
        <div class="controls-section">
          <div class="control-group">
            <span class="mode-lbl">Mode:</span>
            <select class="mode-sel-hero" [(ngModel)]="selectedMode" (ngModelChange)="onModeChange($event)">
              <option value="qa">💬  Q&amp;A</option>
              <option value="translator">🌐  Translator</option>
              <option value="resume">📄  Resume Analyzer</option>
              <option value="question_paper">📚  Question Paper</option>
              <option value="legal">⚖️  Legal Simplifier</option>
              <option value="medical">🩺  Medical Report</option>
            </select>
          </div>
          <button class="incognito-toggle-hero" [class.on]="chatSvc.incognito()" (click)="toggleIncognito()">
            🕵️ Incognito
          </button>
        </div>
      </div>
    </div>

    <!-- CHAT AREA -->
    <div class="chat-area" #chatArea>
      @if (!chatSvc.currentChat() || !chatSvc.messages().length) {
        <div class="empty-state">
          <div class="empty-icon">{{ chatSvc.currentChat() ? '📂' : '💬' }}</div>
          <div class="empty-title">{{ chatSvc.currentChat() ? 'Ready to analyze' : 'No chat selected' }}</div>
          <div class="empty-sub">{{ chatSvc.currentChat() ? 'Upload a document and start chatting.' : 'Create a new chat or pick one from the sidebar.' }}</div>
        </div>
      }
      @for (msg of chatSvc.messages(); track $index) {
        <div class="msg-group" [class.user]="msg.role==='user'" [class.ai]="msg.role==='assistant'">
          <div class="msg-av" [class.u]="msg.role==='user'" [class.a]="msg.role==='assistant'">
            {{ msg.role === 'user' ? authSvc.userInitial : '🤖' }}
          </div>
          <div class="msg-container">
            <div class="msg-bubble" [innerHTML]="fmtMsg(msg.content)">
            </div>
            <button class="delete-msg-btn" title="Delete message" (click)="deleteMessage($index)">✕</button>
          </div>
        </div>
        @if (msg.role === 'assistant' && msg.metrics) {
          <div class="metrics-row">
            <div class="m-chip blue">⚡ {{ msg.metrics.latency_ms }}ms</div>
            <div class="m-chip green">📊 {{ msg.metrics.chunks_retrieved }} chunks retrieved</div>
            <div class="m-chip purple">🎯 Relevance: {{ (msg.metrics.avg_relevance_score * 100) | number:'1.0-0' }}%</div>
          </div>
        }
      }
      @if (chatSvc.isTyping()) {
        <div class="msg-group ai">
          <div class="msg-av a">🤖</div>
          <div class="msg-bubble" style="padding:0">
            <div class="typing-row">
              <div class="t-dot"></div><div class="t-dot"></div><div class="t-dot"></div>
            </div>
          </div>
        </div>
      }
    </div>

    <!-- INPUT AREA -->
    <div class="input-area"
         [class.dragging-over]="isDragging"
         (dragover)="onDragOver($event)"
         (dragleave)="onDragLeave($event)"
         (drop)="onDrop($event)">
      <input #fileInput type="file" style="display:none"
             accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" multiple
             (change)="onFileChange($event)">

      <!-- FILE CHIPS -->
      @if (fileChips.length) {
        <div class="chips-row">
          @for (chip of fileChips; track chip.id) {
            <div class="file-chip">
              📎 {{ chip.name }}
              <span [style.opacity]="chip.done ? 1 : 0.6"
                    [style.color]="chip.error ? 'var(--c-danger)' : chip.done ? 'var(--c-success)' : 'inherit'"
                    style="font-size:12px">
                {{ chip.status }}
              </span>
            </div>
          }
        </div>
      }

      <!-- UPLOADED FILES SECTION -->
      @if (uploadedFiles.length) {
        <div class="uploaded-files-section">
          <div class="uploaded-files-label">📂 Uploaded Files</div>
          <div class="uploaded-files-list">
            @for (file of uploadedFiles; track file.id) {
              <div class="uploaded-file-item">
                <div class="file-info">
                  <span class="file-name">📄 {{ file.name }}</span>
                  <span class="file-chunks">{{ file.chunks }} chunks</span>
                </div>
                <button class="remove-file-btn" title="Remove file" (click)="deleteUploadedFile(file.id)">🗑️</button>
              </div>
            }
          </div>
        </div>
      }

      <!-- TEXT INPUT ROW -->
      <div class="input-row">
        <button class="icon-btn" title="Attach file" (click)="fileInput.click()">📎</button>
        <textarea #msgInput class="msg-input" rows="1"
          [placeholder]="selectedMode === 'medical' ? 'Upload medical report — auto-analyzed' : 'Type your message...'"
          [disabled]="selectedMode === 'medical'"
          [(ngModel)]="msgText"
          (keydown)="onKey($event)"
          (input)="autoH($event)">
        </textarea>
        <button class="icon-btn" [class.recording]="isRecording" title="Voice input" (click)="toggleVoice()">🎤</button>
        <button class="send-btn" [disabled]="chatSvc.isTyping()" (click)="sendMsg()">➤</button>
      </div>

      <!-- DELETE FILE CONFIRMATION -->
      @if (deleteConfirmFileId) {
        <div class="delete-confirm-overlay" (click)="cancelDeleteFile()">
          <div class="delete-confirm-dialog" (click)="$event.stopPropagation()">
            <div class="delete-confirm-icon">🗑️</div>
            <div class="delete-confirm-title">Remove File?</div>
            <div class="delete-confirm-text">This file will be removed from the chat. You can upload it again if needed.</div>
            <div class="delete-confirm-actions">
              <button class="btn-cancel" (click)="cancelDeleteFile()">Cancel</button>
              <button class="btn-delete" (click)="confirmDeleteFile()">Remove</button>
            </div>
          </div>
        </div>
      }

      <!-- DELETE MESSAGE CONFIRMATION -->
      @if (deleteConfirmMsgIndex !== null) {
        <div class="delete-confirm-overlay" (click)="cancelDeleteMessage()">
          <div class="delete-confirm-dialog" (click)="$event.stopPropagation()">
            <div class="delete-confirm-icon">🗑️</div>
            <div class="delete-confirm-title">Delete Message?</div>
            <div class="delete-confirm-text">This message will be permanently removed from the chat.</div>
            <div class="delete-confirm-actions">
              <button class="btn-cancel" (click)="cancelDeleteMessage()">Cancel</button>
              <button class="btn-delete" (click)="confirmDeleteMessage()">Delete</button>
            </div>
          </div>
        </div>
      }

      <!-- DELETE CHAT CONFIRMATION -->
      @if (deleteConfirmChatId) {
        <div class="delete-confirm-overlay" (click)="cancelDeleteChat()">
          <div class="delete-confirm-dialog" (click)="$event.stopPropagation()">
            <div class="delete-confirm-icon">🗑️</div>
            <div class="delete-confirm-title">Delete Chat?</div>
            <div class="delete-confirm-text">This chat and all its messages will be permanently deleted. This action cannot be undone.</div>
            <div class="delete-confirm-actions">
              <button class="btn-cancel" (click)="cancelDeleteChat()">Cancel</button>
              <button class="btn-delete" (click)="confirmDeleteChat()">Delete</button>
            </div>
          </div>
        </div>
      }

    </div>
  </div>
</div>
  `
})
export class AppShellComponent implements OnInit, AfterViewChecked {
  @ViewChild('chatArea') chatAreaEl!: ElementRef<HTMLDivElement>;
  @ViewChild('msgInput') msgInputEl!: ElementRef<HTMLTextAreaElement>;

  authSvc = inject(AuthService);
  chatSvc = inject(ChatService);
  toast   = inject(ToastService);
  sanitizer = inject(DomSanitizer);

  apiUrl = environment.apiUrl;

  selectedMode = 'qa';
  msgText      = '';
  showProfile  = false;
  activeModal  = '';
  isDragging   = false;
  isRecording  = false;
  fileChips: FileChip[] = [];
  uploadedFiles: UploadedFile[] = [];
  chipId = 0;
  deleteConfirmFileId: string | null = null;
  deleteConfirmMsgIndex: number | null = null;
  deleteConfirmChatId: string | null = null;

  newUsername = '';
  curPwd = ''; newPwd = '';

  private recognition: any = null;
  private needsScroll = false;

  ngOnInit(): void {
    this.chatSvc.loadChats().subscribe();
    this.authSvc.fetchProfile().subscribe();
    this.initVoice();
  }

  ngAfterViewChecked(): void {
    if (this.needsScroll && this.chatAreaEl) {
      this.chatAreaEl.nativeElement.scrollTop = this.chatAreaEl.nativeElement.scrollHeight;
      this.needsScroll = false;
    }
  }

  // ── Global paste listener ─────────────────────────────────────────────
  @HostListener('window:paste', ['$event'])
  onPaste(e: ClipboardEvent): void {
    if (!this.authSvc.token()) return;
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of Array.from(items)) {
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) { e.preventDefault(); this.processFile(file); return; }
      }
    }
  }

  // ── TOP BAR ───────────────────────────────────────────────────────────
  openDocs(): void { window.open(this.apiUrl + '/docs', '_blank'); }
  openApi():  void { window.open(this.apiUrl + '/redoc', '_blank'); }

  toggleProfile(e: Event): void { e.stopPropagation(); this.showProfile = !this.showProfile; }
  closeProfile(e: MouseEvent): void {
    if ((e.target as HTMLElement).classList.contains('overlay')) this.showProfile = false;
  }

  openModal(name: string): void { this.activeModal = name; this.showProfile = false; }
  closeModal(): void { this.activeModal = ''; }

  uploadPic(e: Event): void {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.authSvc.uploadProfilePic(file).subscribe({
      next: () => this.toast.show('Profile picture updated ✅', 'ok'),
      error: () => this.toast.show('Upload failed', 'err')
    });
  }

  saveUsername(): void {
    if (!this.newUsername) { this.toast.show('Name cannot be empty', 'err'); return; }
    this.authSvc.changeUsername(this.newUsername).subscribe({
      next: () => { this.closeModal(); this.toast.show('Username updated ✅', 'ok'); this.newUsername = ''; },
      error: err => this.toast.show(err.error?.detail || 'Failed', 'err')
    });
  }

  savePassword(): void {
    if (!this.curPwd || !this.newPwd) { this.toast.show('Fill all fields', 'err'); return; }
    this.authSvc.changePassword(this.curPwd, this.newPwd).subscribe({
      next: () => { this.closeModal(); this.toast.show('Password changed ✅', 'ok'); this.curPwd = ''; this.newPwd = ''; },
      error: err => this.toast.show(err.error?.detail || 'Failed', 'err')
    });
  }

  // ── SIDEBAR ───────────────────────────────────────────────────────────
  createChat(): void {
    this.chatSvc.createChat('New Chat', this.selectedMode).subscribe({
      error: () => this.toast.show('Failed to create chat', 'err')
    });
  }

  delChat(e: Event, chatId: string): void {
    e.stopPropagation();
    this.deleteConfirmChatId = chatId;
  }

  confirmDeleteChat(): void {
    if (!this.deleteConfirmChatId) return;
    this.chatSvc.deleteChat(this.deleteConfirmChatId).subscribe({
      next: () => this.toast.show('Chat deleted', 'ok'),
      error: () => this.toast.show('Delete failed', 'err')
    });
    this.deleteConfirmChatId = null;
  }

  cancelDeleteChat(): void {
    this.deleteConfirmChatId = null;
  }

  // ── MODE ──────────────────────────────────────────────────────────────
  onModeChange(mode: string): void {
    this.chatSvc.currentMode.set(mode);
  }

  toggleIncognito(): void {
    this.chatSvc.toggleIncognito();
    this.toast.show(
      this.chatSvc.incognito() ? '🕵️ Incognito ON — nothing will be saved' : 'Incognito mode off', 'ok'
    );
  }

  // ── FILE UPLOAD ───────────────────────────────────────────────────────
  onDragOver(e: DragEvent): void  { e.preventDefault(); this.isDragging = true; }
  onDragLeave(e: DragEvent): void { e.preventDefault(); this.isDragging = false; }
  onDrop(e: DragEvent): void {
    e.preventDefault(); this.isDragging = false;
    Array.from(e.dataTransfer?.files || []).forEach(f => this.processFile(f));
  }
  onFileChange(e: Event): void {
    const files = (e.target as HTMLInputElement).files;
    if (files) Array.from(files).forEach(f => this.processFile(f));
    (e.target as HTMLInputElement).value = '';
  }

  async processFile(file: File): Promise<void> {
    // Auto-create chat if none selected
    if (!this.chatSvc.currentChat()) {
      await new Promise<void>((res, rej) => {
        const title = file.name.replace(/\.[^.]+$/, '') || 'New Chat';
        this.chatSvc.createChat(title, this.selectedMode).subscribe({ next: () => res(), error: () => rej() });
      });
    }

    const id = ++this.chipId;
    const chip: FileChip = { id, name: file.name, status: 'Uploading…', done: false, error: false };
    this.fileChips.push(chip);

    const chatId = this.chatSvc.currentChat()!.chat_id;
    this.chatSvc.uploadFile(file, chatId).subscribe({
      next: res => {
        chip.status = `✓ ${res.chunks_added} chunks indexed`;
        chip.done   = true;
        if (res.incognito && res.session_id) this.chatSvc.incognitoSid.set(res.session_id);
        this.toast.show(`✅ ${file.name} indexed (${res.chunks_added} chunks)`, 'ok');
        // Add to uploaded files
        const uploadedFile: UploadedFile = {
          id: crypto.randomUUID(),
          name: file.name,
          chunks: res.chunks_added,
          uploadedAt: new Date().toISOString()
        };
        this.uploadedFiles.push(uploadedFile);
        // Remove chip after 3.5s
        setTimeout(() => { this.fileChips = this.fileChips.filter(c => c.id !== id); }, 3500);
        // Auto-send for medical mode
        if (this.selectedMode === 'medical') this.sendMsg(true);
      },
      error: err => {
        chip.status = err.error?.detail || 'Failed';
        chip.error  = true;
        this.toast.show(err.error?.detail || 'Upload failed', 'err');
      }
    });
  }

  // ── SEND MESSAGE ──────────────────────────────────────────────────────
  deleteUploadedFile(fileId: string): void {
    this.deleteConfirmFileId = fileId;
  }

  confirmDeleteFile(): void {
    if (!this.deleteConfirmFileId) return;
    this.uploadedFiles = this.uploadedFiles.filter(f => f.id !== this.deleteConfirmFileId);
    this.toast.show('File removed from chat', 'ok');
    this.deleteConfirmFileId = null;
  }

  cancelDeleteFile(): void {
    this.deleteConfirmFileId = null;
  }

  // ── DELETE CHAT MESSAGE ───────────────────────────────────────────────
  deleteMessage(index: number): void {
    this.deleteConfirmMsgIndex = index;
  }

  confirmDeleteMessage(): void {
    if (this.deleteConfirmMsgIndex === null) return;
    const messages = this.chatSvc.messages();
    messages.splice(this.deleteConfirmMsgIndex, 1);
    this.chatSvc.messages.set([...messages]);
    this.toast.show('Message deleted', 'ok');
    this.deleteConfirmMsgIndex = null;
  }

  cancelDeleteMessage(): void {
    this.deleteConfirmMsgIndex = null;
  }

  sendMsg(autoMedical = false): void {
    if (!this.chatSvc.currentChat()) { this.toast.show('Create a chat first', 'err'); return; }
    const query = autoMedical ? '' : this.msgText.trim();
    if (this.selectedMode !== 'medical' && !query) return;

    if (query) {
      const userMsg: Message = { role: 'user', content: query, created_at: new Date().toISOString() };
      this.chatSvc.messages.update(m => [...m, userMsg]);
      this.msgText = '';
      if (this.msgInputEl) this.msgInputEl.nativeElement.style.height = 'auto';
    }
    this.needsScroll = true;

    this.chatSvc.sendMessage({
      chat_id: this.chatSvc.currentChat()!.chat_id,
      mode: this.selectedMode,
      query,
      incognito: this.chatSvc.incognito(),
      incognito_session_id: this.chatSvc.incognitoSid() || ''
    }).subscribe({
      next: res => {
        const aiMsg: Message = {
          role: 'assistant',
          content: res.answer,
          created_at: new Date().toISOString(),
          metrics: res.retrieval_metrics
        };
        this.chatSvc.messages.update(m => [...m, aiMsg]);
        this.needsScroll = true;

        // Auto-update sidebar title from first message
        const chat = this.chatSvc.currentChat();
        if (chat && (chat.title === 'New Chat' || !chat.title) && query) {
          const title = query.slice(0, 50) + (query.length > 50 ? '...' : '');
          this.chatSvc.updateChatTitle(chat.chat_id, title);
        }
      },
      error: err => this.toast.show(err.error?.detail || 'Error', 'err')
    });
  }

  // ── VOICE ─────────────────────────────────────────────────────────────
  initVoice(): void {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    this.recognition = new SR();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
    this.recognition.onresult = (e: any) => {
      this.msgText += e.results[0][0].transcript;
      this.stopVoice();
    };
    this.recognition.onerror = this.recognition.onend = () => this.stopVoice();
  }

  toggleVoice(): void {
    if (!this.recognition) { this.toast.show('Voice not supported in this browser', 'err'); return; }
    this.isRecording ? this.stopVoice() : this.startVoice();
  }
  startVoice(): void { this.isRecording = true; this.recognition.start(); this.toast.show('🎤 Listening…', 'ok'); }
  stopVoice():  void { this.isRecording = false; this.recognition?.stop(); }

  // ── UTILS ─────────────────────────────────────────────────────────────
  onKey(e: KeyboardEvent): void {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.sendMsg(); }
  }

  autoH(e: Event): void {
    const el = e.target as HTMLTextAreaElement;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }

  fmtMsg(content: string): SafeHtml {
    if (!content) return this.sanitizer.sanitize(1, '') || '';
    
    let html = content
      // Escape HTML special chars first
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      // Headers
      .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
      .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
      .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Code blocks
      .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
      // Inline code
      .replace(/`(.*?)`/g, '<code>$1</code>')
      // Lists
      .replace(/^\* (.*?)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      // Line breaks - collapse multiple newlines to single br
      .replace(/\n\n+/g, '<br>')
      .replace(/\n/g, ' ');
    
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  timeAgo(dt: string | null): string {
    if (!dt) return '';
    const diff = Date.now() - new Date(dt).getTime();
    if (diff < 60000)    return 'just now';
    if (diff < 3600000)  return Math.floor(diff / 60000) + 'm ago';
    if (diff < 86400000) return new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return new Date(dt).toLocaleDateString([], { month: 'short', day: 'numeric' });
  }

  chatColor(id: string): string {
    const p = ['#dbeafe', '#ede9fe', '#d1fae5', '#fef3c7', '#fce7f3', '#fee2e2'];
    return p[parseInt(id.replace(/-/g, '').slice(-2), 16) % p.length];
  }
}
