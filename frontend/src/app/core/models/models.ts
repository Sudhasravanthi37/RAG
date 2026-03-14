export interface User {
  user_id: string;
  name: string;
  email: string;
  profile_pic_url: string;
  is_email_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface Chat {
  chat_id: string;
  title: string;
  last_message_at: string | null;
  created_at: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  metrics?: RetrievalMetrics;
}

export interface RetrievalMetrics {
  latency_ms: number;
  chunks_retrieved: number;
  total_chunks_in_store: number;
  relevance_scores: number[];
  avg_relevance_score: number;
}

export interface SendMessageResponse {
  answer: string;
  incognito: boolean;
  retrieval_metrics: RetrievalMetrics;
}

export interface UploadResponse {
  message: string;
  filename: string;
  doc_id?: string;
  chat_id: string;
  auto_created_chat?: boolean;
  chunks_added: number;
  total_chunks_in_store: number;
  incognito: boolean;
  session_id?: string;
}

export interface Toast {
  id: number;
  message: string;
  type: '' | 'ok' | 'err' | 'warn';
}
