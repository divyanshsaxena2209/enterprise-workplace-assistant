# Enterprise Workplace Assistant - Startup Instructions

To run the complete application locally, you will need to open **two separate terminal windows** and run one of the following sets of commands in each:

### 2. Start the Backend API (FastAPI)
This handles authentication, database logic, and AI integrations.
```powershell
.\backend\venv\Scripts\Activate.ps1
python backend/start_backend.py
```

### 3. Start the Frontend Application (Next.js)
This serves the user interface.
```powershell
cd frontend
npm run dev
```

---
*Note: Make sure your current working directory is the root of the project (`enterprise-workplace-assistant`) before running these.*
