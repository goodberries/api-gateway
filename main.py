from fastapi import FastAPI, HTTPException
import boto3
import os

app = FastAPI()

# In a real app, this would be a more robust service discovery mechanism
BOT_SERVICE_URL = "http://localhost:8001" 

@app.post("/chat")
async def forward_to_bot_service(query: str):
    """
    Receives a user query and forwards it to the Bot Service.
    """
    try:
        # This is a placeholder for a more robust async HTTP client
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BOT_SERVICE_URL}/process_query", json={"query": query})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to Bot Service: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
