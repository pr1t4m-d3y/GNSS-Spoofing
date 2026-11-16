# 🚀 GNSS Security Shield — Run Guide

Follow these steps to launch the system locally in VS Code.

---

### 1. Open the Project
- Open **VS Code**.
- Select **File > Open Folder...** and choose the root directory:
  `/Users/atharv/Downloads/GNSS_Security_Package/GNSS_Security_Package`

---

### 2. Start the Backend (FastAPI)
Open a new terminal in VS Code (**Terminal > New Terminal**) and run:

```bash
# 1. Navigate to backend
cd backend

# 2. Activate Virtual Environment (if it exists)
source venv/bin/activate

# 3. Start the server
python3 main.py
```
> [!TIP]
> The backend will run at `http://localhost:8000`. Keep this terminal open!

---

### 3. Start the Frontend (Next.js)
Open a **second terminal** in VS Code (click the `+` icon in the terminal panel) and run:

```bash
# 1. Navigate to frontend
cd frontend

# 2. Start the development server
npm run dev
```
> [!TIP]
> The dashboard will be available at `http://localhost:3000`.

---

### 4. Configuration & Troubleshooting
- **Python Version**: Ensure you're using `Python 3.9` or `3.10` for best compatibility with `scikit-learn`.
- **Environment**: If `source venv/bin/activate` fails, make sure you've installed dependencies with `pip install -r requirements.txt`.
- **Ports**: If you see "Address already in use," it means a previous session is still running. You can kill them by running:
  - `killall -9 python3`
  - `killall -9 node`

---

### 📂 Important Files
- `backend/main.py`: The API and logic engine.
- `frontend/src/app/page.tsx`: The main dashboard UI.
- `generate_test_data.py`: Run this if you need new `.csv` files for testing.
