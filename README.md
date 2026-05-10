# 🔍 PHANTOM.EYE — AI Image Forensics Detector

A cybersecurity-themed web app that analyzes images and determines whether they are **AI-generated or authentic**, powered by Claude Sonnet.

---

## ✨ Features

- Upload any JPEG, PNG, WEBP, or GIF image
- Get an **AI probability score** (0–100%)
- Detailed **forensic breakdown** of detected indicators
- Analysis of textures, lighting, geometry, and artifacts
- Cyberpunk / hacker terminal UI
- Fully free to host on Render

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python + FastAPI |
| AI Engine | Anthropic Claude Sonnet |
| Frontend | HTML/CSS/JS (no framework) |
| Hosting | Render (free tier) |

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/phantom-eye.git
cd phantom-eye
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your API key
```bash
# Linux/Mac
export ANTHROPIC_API_KEY=your_key_here

# Windows PowerShell
$env:ANTHROPIC_API_KEY="your_key_here"
```

Get your free API key at: https://console.anthropic.com

### 5. Run the app
```bash
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

---

## ☁️ Deploy on Render (Free Hosting)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) and sign up (free)
3. Click **New → Web Service**
4. Connect your GitHub repo
5. Render auto-detects `render.yaml` — just click **Deploy**
6. Go to **Environment** tab → add:
   - Key: `ANTHROPIC_API_KEY`
   - Value: your Claude API key
7. Your app is live at `https://phantom-eye.onrender.com` (or similar)

> ⚠️ Free tier on Render spins down after inactivity — first load may take ~30 seconds.

---

## 📁 Project Structure

```
phantom-eye/
├── main.py              # FastAPI backend + Claude API integration
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── Procfile             # Process config
├── templates/
│   └── index.html       # Full frontend (HTML/CSS/JS)
└── static/              # Static assets (empty, extendable)
```

---

## 🔐 How It Works

1. User uploads an image
2. Image is base64-encoded and sent to Claude Sonnet via the Anthropic API
3. Claude performs visual forensic analysis:
   - Texture coherence
   - Lighting/shadow consistency
   - Geometric anomalies (hands, text, patterns)
   - Background artifacts
   - Over-smoothing / rendering artifacts
4. Returns JSON: verdict, confidence score, indicators, summary
5. Frontend renders results with animated bars and indicator cards

---

## ⚠️ Disclaimer

Results are **probabilistic** and should be used as an investigative aid, not absolute truth. No AI detector is 100% accurate.

---

## 👨‍💻 Built by

**[Your Name]** — CSE Student | Cybersecurity Enthusiast

Portfolio: [your-portfolio-link]  
GitHub: [@your-username]
