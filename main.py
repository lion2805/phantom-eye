from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import base64
import os
import json

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

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not set on the server.")

    client = anthropic.Anthropic(api_key=api_key)

    image_data = base64.standard_b64encode(contents).decode("utf-8")
    media_type = file.content_type

    prompt = """You are an expert forensic image analyst specializing in detecting AI-generated images.
Analyze this image thoroughly and determine if it is AI-generated or a real/authentic photograph.

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

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        raw = response.content[0].text.strip()
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
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="Invalid Anthropic API key. Check ANTHROPIC_API_KEY in Render.")
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {type(e).__name__}: {str(e)}")
