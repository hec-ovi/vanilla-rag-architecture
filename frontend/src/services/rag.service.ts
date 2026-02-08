import type { QueryRequest, QueryResponse, IngestResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ChatResponse {
  answer: string;
  sources: Array<{
    chunk_id: string;
    doc_id: string;
    filename: string;
    content: string;
    score: number;
    index: number;
  }>;
  query: string;
  conversation_id: string;
  model: string;
}

export class RAGService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async health(): Promise<{ status: string; service: string; version: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  }

  async ingest(file: File, onProgress?: (progress: number) => void): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append('file', file);

    if (onProgress) {
      onProgress(50);
    }

    const response = await fetch(`${this.baseUrl}/api/v1/ingest`, {
      method: 'POST',
      body: formData,
    });

    if (onProgress) {
      onProgress(100);
    }

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Ingestion failed');
    }

    return response.json();
  }

  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Query failed');
    }

    return response.json();
  }

  async chat(query: string, conversationId?: string): Promise<ChatResponse> {
    const body: { query: string; conversation_id?: string } = { query };
    if (conversationId) {
      body.conversation_id = conversationId;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Chat failed');
    }

    return response.json();
  }

  async getConversations(): Promise<Array<{ conversation_id: string; message_count: number; updated_at: string }>> {
    const response = await fetch(`${this.baseUrl}/api/v1/conversations`);
    if (!response.ok) {
      throw new Error('Failed to fetch conversations');
    }
    const data = await response.json();
    return data.conversations.map((c: { conversation_id: string; messages: unknown[]; updated_at: string }) => ({
      conversation_id: c.conversation_id,
      message_count: c.messages.length,
      updated_at: c.updated_at,
    }));
  }

  async deleteConversation(conversationId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/conversations/${conversationId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete conversation');
    }
  }

  async reset(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/reset`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Reset failed');
    }

    return response.json();
  }
}

export const ragService = new RAGService();
