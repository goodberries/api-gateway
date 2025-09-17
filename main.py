from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel

app = FastAPI()

# --- CORS Configuration ---
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Service URLs ---
# These are the internal Kubernetes service names //test
BOT_SERVICE_URL = "http://bot-service:8001"
INTERACTIONS_SERVICE_URL = "http://interactions-service:8003"

class Feedback(BaseModel):
    interaction_id: str
    feedback: str # 'like' or 'dislike'

@app.post("/chat")
async def forward_to_bot_service(request: Request):
    """
    Receives a user query, forwards it to the Bot Service, and returns the response.
    The query is passed as a query parameter.
    """
    query = request.query_params.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required.")
        
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request with the query parameter
            response = await client.post(f"{BOT_SERVICE_URL}/chat?query={query}")
            response.raise_for_status()
            # The bot service now returns a JSON with 'response' and 'interaction_id'
            return response.json()
    except httpx.HTTPStatusError as e:
        # Forward the error from the downstream service
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to Bot Service: {str(e)}")

@app.post("/feedback")
async def forward_to_interactions_service(feedback: Feedback):
    """
    Receives feedback from the frontend, transforms it, and forwards it to the Interactions Service.
    """
    # Translate frontend feedback ('like'/'dislike') to backend score (1/-1)
    feedback_score = 1 if feedback.feedback == 'like' else -1

    try:
        feedback_update_url = f"{INTERACTIONS_SERVICE_URL}/interactions/{feedback.interaction_id}/feedback"
        async with httpx.AsyncClient() as client:
            response = await client.patch(feedback_update_url, json={"feedback_score": feedback_score})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to Interactions Service: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
