from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import boto3
import os
from langchain_aws import ChatBedrock

app = FastAPI()

# --- CORS Configuration ---
# For demo purposes, allow all origins.
# In a production environment, you should restrict this to your actual frontend's URL.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# In a real app, this would be a more robust service discovery mechanism
BOT_SERVICE_URL = "http://bot-service:8001"

# Initialize Bedrock client + LLM
bedrock_client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))

# Use ChatBedrock from langchain-aws (future-proof)
llm = ChatBedrock(
    client=bedrock_client,
    model_id="anthropic.claude-3-haiku-20240307-v1:0"
)


@app.post("/chat")
async def forward_to_bot_service(query: str):
    """
    Receives a user query and forwards it to the Bot Service.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BOT_SERVICE_URL}/process_query", json={"query": query})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to Bot Service: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
