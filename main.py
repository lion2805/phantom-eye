from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import base64
import os
from pathlib import Path

app = FastAPI(title="AI Image Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_MB = 5


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use JPEG, PNG, WEBP, or GIF.")

    contents = await file.read()

    # Validate file size
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_SIZE_MB}MB.")

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
- Metadata-level hints (image noise patterns, EXIF anomalies)
- Symmetry that is too perfect or uncanny valley effect
- Blending artifacts at object boundaries

Respond ONLY in this exact JSON format (no extra text, no markdown):
{
  "verdict": "AI-Generated" or "Likely Real" or "Inconclusive",
  "confidence": <integer 0-100>,
  "ai_probability": <integer 0-100>,
  "indicators": [
    {"label": "<short indicator name>", "detail": "<1-2 sentence explanation>", "severity": "high" or "medium" or "low"}
  ],
  "summary": "<2-3 sentence overall analysis explaining the verdict>",
  "metadata_notes": "<brief notes on image quality, resolution, or patterns>"
}"""

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

        import json
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return JSONResponse(content=result)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI analysis response.")
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
