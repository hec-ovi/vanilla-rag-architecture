# 🚀 Vanilla RAG Architecture

A production-ready, local-first **Retrieval-Augmented Generation (RAG)** system that delivers state-of-the-art retrieval accuracy through semantic reranking. Built for developers who want AI-assisted workflows without cloud dependencies.

> **The Breakthrough**: Simple vector retrieval fused with cross-encoder reranking, the "secret sauce" that transforms basic RAG into a precision knowledge engine.

## ✨ Features

- **🔍 Hybrid Retrieval**: Vector search (top-10) + semantic reranking (top-3) for killer precision
- **📄 Dynamic Ingestion**: Upload `.txt`, `.pdf`, `.png/.jpg`, processed and vectorized automatically
- **🖼️ Multimodal Ready**: Images captioned via vision models, treated as queryable documents
- **🤖 Local LLM Power**: Ollama integration with ROCm GPU acceleration (AMD Strix Halo optimized)
- **⚡ Blazing Fast**: Flash Attention + Q8 KV cache quantization for efficient inference
- **🔒 Privacy-Locked**: 100% local, your data never leaves your machine
- **🎨 Sleek UI**: Vite + React frontend with drag-drop upload and real-time streaming

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐     │
│  │  Frontend   │    │   Backend   │    │     Ollama      │     │
│  │  Vite+React │◄──►│   FastAPI   │◄──►│  LLM Inference  │     │
│  │   :3000     │    │    :8000    │    │    :11434       │     │
│  └─────────────┘    └──────┬──────┘    └─────────────────┘     │
│                            │                                    │
│                     ┌──────┴──────┐                            │
│                     │  Vector DB  │                            │
│                     │FAISS/Chroma │                            │
│                     └─────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Vite + React 19 + TypeScript |
| **Backend** | FastAPI + Python 3.12 + UV |
| **Embeddings** | SentenceTransformers (all-MiniLM-L6-v2) |
| **Vector DB** | FAISS (default) / Chroma (toggle) |
| **Reranker** | Cross-encoder (ms-marco-MiniLM-L-6-v2) |
| **LLM Engine** | Ollama (qwen2.5 or gpt-oss) |
| **Vision** | Ollama Vision (llava/qwen2.5-vl) |
| **GPU** | ROCm (AMD Strix Halo gfx1151) |

## 🚀 Quick Start

### Prerequisites

- Ubuntu 25.10+ (Kernel 6.17+)
- Docker with Compose plugin
- AMD GPU with ROCm support (or CPU fallback)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd vanilla-rag-architecture

# Copy and edit environment configuration
cp .env.template .env
# Edit .env with your host paths
```

### 2. Prepare Directories

```bash
# Create data directories (update paths to match your .env)
mkdir -p /home/$USER/models/ollama
mkdir -p /home/$USER/vanilla-rag/data
```

### 3. Launch

```bash
docker compose up -d --build
```

### 4. Verify

```bash
# Check all services are healthy
docker compose ps

# Test Ollama GPU inference
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:14b",
  "prompt": "What is 2+2?",
  "stream": false
}' | jq .

# Test backend
curl http://localhost:8000/health

# Open frontend
open http://localhost:3000
```

## 📁 Project Structure

```
.
├── docker-compose.yml          # Root orchestration
├── .env.template               # Configuration template
├── README.md                   # This file
├── .gitignore                  # Comprehensive ignore rules
├── backend/                    # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py
│       └── ...
├── frontend/                   # Vite React application
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       ├── App.tsx
│       └── ...
└── ollama/                     # ROCm GPU inference service
    ├── Dockerfile
    └── entrypoint.sh
```

## 🔧 Configuration

Key environment variables (see `.env.template` for all options):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODELS_DIR` | (none) | Host path for model storage |
| `DATA_DIR` | (none) | Host path for vector DB and uploads |
| `OLLAMA_MODEL` | `qwen2.5:14b` | LLM model to use |
| `OLLAMA_CONTEXT_LENGTH` | `8192` | Context window size |
| `VECTOR_DB_TYPE` | `faiss` | Vector DB: `faiss` or `chroma` |
| `CHUNK_SIZE` | `500` | Text chunk size |
| `CHUNK_OVERLAP` | `100` | Chunk overlap |
| `TOP_K_RETRIEVE` | `10` | Initial retrieval count |
| `TOP_K_RERANK` | `3` | Final reranked results |

## 🎯 RAG Pipeline

```
User Query
    │
    ▼
┌─────────────────┐
│ Vector Search   │──► Top 10 candidates
│ (Embeddings)    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Cross-Encoder   │──► Top 3 reranked
│ Reranking       │    (Semantic precision)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ LLM Generation  │──► Response + Sources
│ (Context-aware) │
└─────────────────┘
```

## 🧪 Testing RAG

The system includes test data to prove the RAG power:

1. Upload `rag_techniques_test.txt` (auto-generated on first run)
2. Ask obscure questions like: *"What is HyPE vs HyDE in RAG?"*
3. Watch as the system retrieves and answers from context, something base LLMs can't do

## 🛠️ Development

### Backend Only

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

## 📜 License

MIT License, build, modify, deploy freely.

---

**Built with ❤️ for the local AI revolution.**

*If component chaos is killing your workflow, this is your game-changer.*

#RAG #LocalAI #AMD #ROCm #FastAPI #React
