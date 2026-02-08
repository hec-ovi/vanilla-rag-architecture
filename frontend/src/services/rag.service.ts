import type { QueryRequest, QueryResponse, IngestResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

    // Simulate progress since fetch doesn't support upload progress natively
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

  async streamQuery(
    request: QueryRequest,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    // Note: This is a placeholder for streaming implementation
    // The current backend doesn't support streaming yet
    const response = await this.query(request);
    onChunk(response.answer);
  }
}

export const ragService = new RAGService();
