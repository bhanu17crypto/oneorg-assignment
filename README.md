# OneOrg Assessments

Context-Aware RAG Pipeline project.

**Repository structure**
- `backend/`: Python services and pipeline (`main.py`, `rag_pipeline.py`, `document_processor.py`).
- `frontend/my-app`: Frontend application (Vite / React or similar).

**Quick summary**
- **Purpose**: Evaluate document processing and RAG-style pipelines (backend) and a frontend app to interact with the service.

**Prerequisites**
- **Python 3.8+**: Used for the backend.
- **Node.js & npm**: Used for the frontend.
- **Redis** : If the backend uses Redis for caching/queues, ensure a Redis server is available.


**Backend — setup & run**

1. Open a PowerShell in `backend`:

```powershell
cd backend
```

2. Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Set environment variables (examples):

```powershell
$env:PINECONE_API_KEY = 'your_api_key_here'
$env:REDIS_URL = 'redis://localhost:6379'
$env:PINECONE_ENVIRONMENT = 'your_environment'
$env:OPENAI_API_KEY = 'your_api_key_here'
$env:COHERE_API_KEY = 'your_api_key_here'

```

4. Run the backend (the entrypoint is `main.py`):

```powershell
python main.py
```

If your project uses a different entrypoint, check `backend` for the expected script to run (for example `rag_pipeline.py`).

If you need Redis locally, start it with your platform-appropriate command (or run a Docker container):

```powershell
# If you have redis-server available
redis-server
# Or using Docker (if installed)
docker run --name local-redis -p 6379:6379 -d redis:7
```

**Frontend — setup & run**

1. Open a PowerShell in `frontend/my-app`:

```powershell
cd frontend\my-app
```

2. Install dependencies and start the dev server:

```powershell
npm install
npm run dev
```

Note: some projects use `npm run start` or `npm run serve`; if `npm run dev` fails, inspect the `scripts` section in `package.json` to confirm the correct command.

**Run full app**
- 1) Start Redis (ifrom Docker).
- 2) Start the backend in `backend`.
- 3) Start the frontend in `frontend/my-app`.

