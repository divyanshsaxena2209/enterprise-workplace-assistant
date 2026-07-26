# Enterprise Workplace Assistant Platform

AI-Powered Enterprise Workplace Assistant Platform monorepo. This platform serves as a central hub for managing workforce operations, onboarding, and talent acquisition with role-based access controls for Management, HR, and Employees.

## Core Modules & Features

### 1. Profiles & Authentication
- **Role-Based Access Control (RBAC):** Distinct interfaces and permissions for `MANAGEMENT`, `HR`, `ADMIN`, and `EMPLOYEE`.
- **User Profiles:** Integrated employee and management profile management, connecting user identity with their roles and permissions.

### 2. Talent Acquisition Pipeline (ATS)
- **Job Management:** Create, manage, and publish job requisitions.
- **Candidate Tracking:** Track candidates through various stages of the hiring funnel (Applied, Screened, Interviewed, Offered, Hired).
- **Application Management:** Review and score resumes, manage job applications securely.
- **Interview Scheduling:** Log and track interview workflows, notes, and statuses.

### 3. Workforce Onboarding Operations
- **Onboarding Templates:** Standardized templates and task lists for new hires.
- **Employee Progress Tracking:** Employees can view their onboarding checklist and track their progress via an intuitive dashboard.
- **Management Oversight:** HR and Management can monitor the progress of new hires and block/unblock tasks.

### 4. Organizational Intelligence (Knowledge Base)
- **Company Documents:** Centralized storage for company policies, training materials, and documentation.
- **Search & Retrieval:** Fast access to organizational knowledge.

### 5. Custom Dashboards
- **Management Dashboard:** A high-level overview of active jobs, total candidates, applications, and employee count with quick links to manage the organization.
- **Employee Dashboard:** A personalized hub tracking onboarding progress and quick links to their applications and knowledge base.

---

## Project Structure

- `/frontend` - Next.js 15 App Router frontend
- `/backend` - FastAPI Python backend
- `/docs` - Project documentation
- `/scripts` - Automation and helper scripts
- `/supabase` - Database migrations, schema, and configuration for Supabase PostgreSQL.

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
