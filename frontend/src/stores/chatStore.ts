import { create } from 'zustand';
import type { ChatMessage, UploadProgress } from '../types';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  uploads: UploadProgress[];
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  appendToMessage: (id: string, content: string) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  addUpload: (upload: UploadProgress) => void;
  updateUpload: (filename: string, updates: Partial<UploadProgress>) => void;
  removeUpload: (filename: string) => void;
  clearUploads: () => void;
}

const generateId = () => Math.random().toString(36).substring(2, 9);

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  uploads: [],
  
  addMessage: (message) => {
    const newMessage: ChatMessage = {
      ...message,
      id: generateId(),
      timestamp: new Date(),
    };
    set((state) => ({
      messages: [...state.messages, newMessage],
    }));
    return newMessage.id;
  },
  
  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },
  
  appendToMessage: (id, content) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content: msg.content + content } : msg
      ),
    }));
  },
  
  clearMessages: () => set({ messages: [], isLoading: false }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  addUpload: (upload) => {
    set((state) => ({
      uploads: [...state.uploads.filter(u => u.filename !== upload.filename), upload],
    }));
  },
  
  updateUpload: (filename, updates) => {
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.filename === filename ? { ...u, ...updates } : u
      ),
    }));
  },
  
  removeUpload: (filename) => {
    set((state) => ({
      uploads: state.uploads.filter((u) => u.filename !== filename),
    }));
  },
  
  clearUploads: () => set({ uploads: [] }),
}));
