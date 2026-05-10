from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
import json
import httpx

app = FastAPI(title="AI Image Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 5


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use JPEG, PNG, WEBP, or GIF.")

    contents = await file.read()

    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_SIZE_MB}MB.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set on the server.")

    image_data = base64.standard_b64encode(contents).decode("utf-8")
    media_type = file.content_type

    prompt = """You are an expert forensic image analyst specializing in detecting AI-generated images.
Analyze this image thoroughly and determine if it is AI-generated or a real/authentic photograph.

Look for these indicators:
- Unnatural textures (skin, hair, fabric, background)
- Lighting inconsistencies or impossible shadows
- Geometric anomalies (hands with wrong finger count, distorted text, warped patterns)
- Over-smoothing or hyper-realistic rendering artifacts
- Background incoherence or copy-paste-like repetition
- Symmetry that is too perfect or uncanny valley effect
- Blending artifacts at object boundaries

Respond ONLY in this exact JSON format (no extra text, no markdown backticks):
{
  "verdict": "AI-Generated",
  "confidence": 90,
  "ai_probability": 90,
  "indicators": [
    {"label": "Example", "detail": "Example detail here.", "severity": "high"}
  ],
  "summary": "Your 2-3 sentence summary here.",
  "metadata_notes": "Your metadata notes here."
}

verdict must be exactly one of: AI-Generated, Likely Real, Inconclusive."""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": media_type,
                            "data": image_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1000
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        return JSONResponse(content=result)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)} | Raw: {raw[:200]}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e.response.text[:200]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {type(e).__name__}: {str(e)}")
