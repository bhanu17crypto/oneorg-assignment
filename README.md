# Full Stack Application (FastAPI + Vite React)

This repository contains both the **Frontend (Vite + React)** and **Backend (FastAPI)** parts of the application.

---

## 📦 Project Structure
root/
│
├── frontend/ # Vite + React
└── backend/ # FastAPI

yaml
Copy code

---

# Frontend (Vite + React)

###  Install Dependencies
```bash
cd frontend
npm install
Run Development Server
bash
Copy code
npm run dev
Build for Production
bash
Copy code
npm run build

Backend (FastAPI)
Create Virtual Environment & Install Dependencies
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

Run Backend
uvicorn main:app --reload

 Create .env in /backend
OPENAI_API_KEY=your_key
REDIS_HOST=localhost
REDIS_PORT=6379
PINECONE_API_KEY=your_key

 .gitignore for Backend
venv
__pycache__
.env
*.pyc



How to Run Full Project
# Start Backend
cd backend
uvicorn main:app --reload

# Start Frontend
cd frontend
npm run dev
