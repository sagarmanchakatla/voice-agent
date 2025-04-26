# app.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal, Union, Dict, Any
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Creator API", description="Unified API for creating agents across multiple providers")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for request validation
class AgentCreationRequest(BaseModel):
    provider: Literal["vapi", "retell"] = Field(..., description="The provider to use for agent creation")
    name: str = Field(..., description="Name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    model: str = Field(..., description="LLM model to use")
    voice_id: str = Field(..., description="ID of the voice to use")
    system_prompt: str = Field(..., description="System prompt/instructions for the agent")
    initial_message: Optional[str] = Field(None, description="Initial message the agent will say")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for agent interactions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the agent")

class AgentCreationResponse(BaseModel):
    provider: str
    agent_id: str
    name: str
    status: str
    raw_response: Dict[str, Any]

# Provider API clients
class VapiClient:
    BASE_URL = "https://api.vapi.ai/"
    
    def __init__(self):
        self.api_key = os.getenv("VAPI_API_PRIVATE_KEY")
        if not self.api_key:
            raise ValueError("VAPI_API_PRIVATE_KEY environment variable is not set")
    
    async def create_agent(self, data: AgentCreationRequest) -> Dict[str, Any]:
        # Map unified fields to Vapi-specific fields
        vapi_payload = {
            "name": data.name,
            "model": data.model,
            "voice_id": data.voice_id,
            "system_prompt": data.system_prompt,
        }
        
        # Add optional fields
        if data.description:
            vapi_payload["description"] = data.description
        
        if data.initial_message:
            vapi_payload["initial_message"] = data.initial_message
            
        if data.webhook_url:
            vapi_payload["webhook_url"] = data.webhook_url
            
        if data.metadata:
            vapi_payload["metadata"] = data.metadata
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/assistants",
                json=vapi_payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Vapi API Error: {response.text}"
                )
                
            return response.json()

class RetellClient:
    BASE_URL = "https://api.retellai.com"
    
    def __init__(self):
        self.api_key = os.getenv("RETELL_API_KEY")
        if not self.api_key:
            raise ValueError("RETELL_API_KEY environment variable is not set")
    
    async def create_agent(self, data: AgentCreationRequest) -> Dict[str, Any]:
        # Map unified fields to Retell-specific fields
        retell_payload = {
            "agent_name": data.name,
            "voice_id": data.voice_id,
            "llm_model": data.model,
            "llm_system_prompt": data.system_prompt,
            "responce_engine": "llm"
        }
        
        # Add optional fields
        if data.webhook_url:
            retell_payload["llm_webhook_url"] = data.webhook_url
            
        if data.initial_message:
            retell_payload["first_message"] = data.initial_message
            
        if data.description:
            # Retell doesn't have a direct description field, 
            # we can add it to metadata or ignore it
            if not retell_payload.get("metadata"):
                retell_payload["metadata"] = {}
            retell_payload["metadata"]["description"] = data.description
            
        if data.metadata:
            if not retell_payload.get("metadata"):
                retell_payload["metadata"] = {}
            retell_payload["metadata"].update(data.metadata)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/create-agent",
                json=retell_payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Retell API Error: {response.text}"
                )
                
            return response.json()

# Dependency injection
def get_vapi_client():
    return VapiClient()

def get_retell_client():
    return RetellClient()

# Main API endpoint
@app.post("/create-agent", response_model=AgentCreationResponse)
async def create_agent(
    data: AgentCreationRequest,
    vapi_client: VapiClient = Depends(get_vapi_client),
    retell_client: RetellClient = Depends(get_retell_client)
):
    try:
        if data.provider == "vapi":
            response = await vapi_client.create_agent(data)
            return AgentCreationResponse(
                provider="vapi",
                agent_id=response.get("id", ""),
                name=response.get("name", data.name),
                status="success",
                raw_response=response
            )
            
        elif data.provider == "retell":
            response = await retell_client.create_agent(data)
            return AgentCreationResponse(
                provider="retell",
                agent_id=response.get("agent_id", ""),
                name=response.get("agent_name", data.name),
                status="success",
                raw_response=response
            )
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider")
            
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)