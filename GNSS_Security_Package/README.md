# 🛰️ GNSS Security Shield (Antigravity Edition)

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

**GNSS Security Shield** is a high-fidelity, real-time anti-spoofing system designed to protect Global Navigation Satellite Systems from sophisticated Signal Injection Attacks (SIA). By leveraging Isolation Forest machine learning and a modern "Bento Box" dashboard, it provides a comprehensive security overview for critical infrastructure navigation.

---

## ✨ Key Features

- **🧠 AI-Driven Detection**: Utilizes an Isolation Forest model trained on 35+ signal features to identify anomalies in real-time.
- **📊 Live Monitoring Dashboard**: A high-performance Next.js interface with real-time signal charts, interactive satellite maps, and health scoring.
- **🔄 Rolling Window Analysis**: Uses a history-aware feature engineering pipeline to detect subtle drift and spoofing patterns.
- **📁 Batch Analysis**: Drag-and-drop support for analyzing historical GNSS telemetry logs (CSV/XLS).
- **🛠️ Manual Injection Simulation**: Test system resilience by manually injecting signal parameters (Doppler, pseudorange, etc.).

---

## 🏗️ Architecture

- **Backend**: FastAPI (Python) + Scikit-learn + Pandas.
- **Frontend**: Next.js 14 + Tailwind CSS + Framer Motion.
- **Data Science**: original research and training pipeline preserved in `GNSS_Hackathon.ipynb`.

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install xlrd  # For historical data analysis
python3 main.py
```
*Backend runs at `http://localhost:8000`*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Dashboard available at `http://localhost:3000`*

---

## 📂 Project Structure

```text
├── backend/              # FastAPI Logic & AI Engine
│   ├── main.py           # API Endpoints & Inference
│   └── utils.py          # Feature Engineering & History Management
├── frontend/             # Next.js Dashboard
│   ├── src/app/          # Main UI Pages
│   └── src/components/   # Modular UI Components
├── GNSS_Hackathon.ipynb  # original Data Science Research
├── train.xls             # Baseline Dataset
└── README.md             # Project Documentation
```

---

## 🛡️ How to Use

1. **Reset System**: Hit the **Reset** button to clear signal history for a fresh sequence.
2. **Inject Test Signals**: Use the sliders in the "Manual Specs" tab. 
    - *Tip*: Doppler ~2761Hz and Pseudorange ~505,867m represent "Genuine" signals.
3. **Monitor Score**: Keep an eye on the "System Security Health". Scores below 80% indicate potential spoofing.
4. **Detailed Logs**: Check the logs tab for a granular breakdown of every anomaly detected.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an issue for any bugs or feature requests.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
