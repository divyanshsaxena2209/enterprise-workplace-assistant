# Enterprise Workplace Assistant Platform

AI-Powered Enterprise Workplace Assistant Platform monorepo.

## Project Structure

- `/frontend` - Next.js 15 App Router frontend
- `/backend` - FastAPI Python backend
- `/docs` - Project documentation
- `/scripts` - Automation and helper scripts

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.10+
- Docker & Docker Compose

### 1. Environment Setup
Copy the `.env.example` to `.env` in the respective directories:
- `cp .env.example ./frontend/.env.local`
- `cp .env.example ./backend/.env`
Fill in the necessary credentials (Supabase, OpenAI).

### 2. Services
Start local services like ChromaDB using Docker:
```bash
docker-compose up -d
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
