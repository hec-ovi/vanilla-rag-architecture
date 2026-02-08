// RAG API Types

export interface IngestResponse {
  doc_id: string;
  filename: string;
  chunk_count: number;
  status: 'success' | 'error';
  message: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
}

export interface Source {
  chunk_id: string;
  doc_id: string;
  filename: string;
  content: string;
  score: number;
  index: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  query: string;
  model: string;
  tokens_used?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}
