import asyncio
import json
import dataclasses
from datetime import datetime
from typing import List

import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from payment_generator import stream_payment_signals
from payment_analyzer import PaymentAnalyzer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

WEBHOOK_URL = "http://localhost:5678/webhook/db3aa95e-6cb0-4108-8907-50f1860d9c28"
analyzer = PaymentAnalyzer(window_size=30)

# In-memory storage for session signals
session_signals: List[dict] = []


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


@app.get("/")
async def read_root():
    return FileResponse("static/index.html")


@app.get("/api/stream")
async def stream_signals(count: int = 100):
    """SSE endpoint that streams payment signals to the frontend."""
    global session_signals
    session_signals = []

    async def event_generator():
        async for signal in stream_payment_signals(base_delay=0.1, count=count):
            data = dataclasses.asdict(signal)
            session_signals.append(data)
            yield f"data: {json.dumps(data, default=json_serial)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/analyze")
async def trigger_analysis():
    """Sends collected signals to the n8n webhook and returns the LLM result."""
    global session_signals

    if not session_signals:
        return {"error": "No signals collected. Run the stream first."}

    prompt = analyzer.generate_analysis_prompt(session_signals)

    try:
        payload = {"prompt": prompt}
        response = requests.post(WEBHOOK_URL, json=payload, timeout=60)

        if 200 <= response.status_code < 300:
            try:
                resp_json = response.json()
                if isinstance(resp_json, dict):
                    content = (
                        resp_json.get("text")
                        or resp_json.get("output")
                        or resp_json.get("message")
                        or json.dumps(resp_json)
                    )
                else:
                    content = str(resp_json)
                return {"result": content}
            except ValueError:
                return {"result": response.text if response.text else "(Empty response)"}
        else:
            return {"error": f"Webhook error {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
