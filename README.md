# Smart HSRP System using AI (Baseline MVP)

An AI-powered system for **High Security Registration Plate (HSRP)** detection and validation using computer vision and backend APIs. This MVP focuses on a clean separation between frontend, backend, and ML pipeline with room for future scalability.

---

## Architecture (MVP)

```
SMART_HSRP/
├── app/                       # Streamlit frontend
│   ├── app.py                 # Entry point
│   ├── utils/                 # Frontend helper functions
│   └── pages/                 # Streamlit multi-page scripts
│
├── backend/                   # Backend FastAPI services
│   ├── api/                   # API endpoints
│   ├── core/                  # Core ML pipeline logic
│   ├── db/                    # Database layer
│   ├── models/                # ML / DB models
│   ├── services/              # Business logic / service layer
│   ├── tests/                 # Unit & integration tests
│   ├── utils/                 # Backend helpers
│   └── main.py                # FastAPI entry point
│
├── config/                    # Configuration and environment settings
│   └── settings.py
│
├── test_images/               # Sample images for testing
├── test_outputs/
│   └── plate_crops/           # Cropped plate outputs from pipeline
│
├── weights/                   # Pretrained ML models
│   ├── helmet_baseline.pt
│   ├── hsrp_cls.pt
│   └── Plate_Baseline.pt
│
├── .env                       # Environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

---

## 🧰 Tech Stack

**Language**: Python

**Frontend**: Streamlit

**Backend**: FastAPI

### AI / ML

* OpenCV
* Deep Learning Models

  * **YOLO** → Helmet Detection & Number Plate Detection
  * **EfficientNet** → HSRP Classification

### Database

* **SQLite** (current MVP setup)
* **PostgreSQL** (configurable for future use)

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Guardian-22/smart-hsrp-system.git
cd smart-hsrp-system
```

### 2️⃣ Create a virtual environment

Using standard `venv`:

```bash
python -m venv .venv
```

Or using `uv` (recommended for faster dependency management):

```bash
uv venv
```

Activate the environment:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If using `uv`, you may also use:

 ```bash
 uv pip install -r requirements.txt
 ```

### 4️⃣ Run the backend (FastAPI)

```bash
uvicorn backend.main:app --reload
```

### 5️⃣ Run the frontend (Streamlit)

```bash
streamlit run app/app.py
```

---

## 📌 Notes

* Model weights are kept local under `weights/` for the MVP.

---
