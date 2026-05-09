

# DocChat AI -Powered RAG Platform

TalkToDoc is a professional-grade Retrieval-Augmented Generation (RAG) platform that allows users to upload PDF documents and have context-aware conversations with them. Built with **Django** and **LangChain**, it demonstrates a production-ready approach to integrating Large Language Models (LLMs) with private data.

## 🚀 Key Features

- **Asynchronous Document Processing:** Uses Celery and Redis to handle PDF text extraction and vector embedding in the background, ensuring a smooth UI experience.
- **Semantic Search:** Implements ChromaDB as a vector store to retrieve the most relevant document snippets for the AI.
- **Data Isolation:** Uses metadata filtering to ensure users can only query their own uploaded documents.
- **Smart Chat History:** Integrated conversation memory that summarizes long chats to stay within LLM token limits.
- **OCR Support:** Integrated Tesseract OCR to handle scanned PDFs that don't contain native text.
- **Reactive UI:** Built with Django Templates and HTMX for a modern, "single-page" feel without the complexity of a heavy JS framework.

## 🛠️ Tech Stack

- **Backend:** Django, Django Rest Framework (DRF)
- **AI/LLM:** LangChain, OpenAI API (GPT-4o), ChromaDB (Vector Store)
- **Task Queue:** Celery, Redis
- **Database:** PostgreSQL (Metadata), AWS S3 (File Storage)
- **Frontend:** HTMX, Tailwind CSS

## 🏗️ Architecture 

1. **Upload:** User uploads PDF -> Django stores file in S3.
2. **Ingest:** Celery picks up the file -> Extracts text -> Chunks text -> Generates Embeddings.
3. **Store:** Embeddings are saved in ChromaDB with `user_id` metadata.
4. **Query:** User asks a question -> System retrieves relevant chunks from ChromaDB -> LLM generates answer based on context.

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Redis Server (for Celery)
- Tesseract OCR (for scanned PDF support)
- OpenAI API Key

### Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/srinu005/DocChat AI.git
   cd DocChat AI