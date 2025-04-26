import requests
import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
load_dotenv()

VAPI_BASE_URL = os.getenv("VAPI_BASE_URL")
RETELL_BASE_URL = os.getenv("RETELL_BASE_URL")

class AgentCreator:
    @staticmethod
    def create_vapi_agent(agent_data):
        URL = f"{VAPI_BASE_URL}/assistant"
        headers = {
            "Authorization": f"Bearer {os.getenv('VAPI_API_PRIVATE_KEY')}",
            "Content-Type": "application/json"
        }

        vapi_payload = {
            "name": agent_data.get("name"),
            "model": {
                "provider": agent_data.get("model_provider", "google"),
                "model": agent_data.get("model_name", "gemini-1.5-pro"),
                "temperature": agent_data.get('temperature', 0.7),
                "systemPrompt": agent_data.get('system_prompt', 'You are a helpful assistant'),
            },
            "voice": {
                "provider": agent_data.get('voice_provider', '11labs'),
                "voiceId": agent_data.get('voice_id', '21m00Tcm4TlvDq8ikWAM'),
            },
            "firstMessage": agent_data.get('first_message', 'Hi, how can I help you?'),
        }

        response = requests.post(URL, json=vapi_payload, headers=headers)
        return response.json(), response.status_code
    

    @staticmethod
    def create_retell_llm(llm_config: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Create a Retell LLM configuration based on documentation"""
        retell_base_url = os.getenv("RETELL_BASE_URL", "https://api.retellai.com")
        url = f"{retell_base_url}/create-retell-llm"
        headers = {
            "Authorization": f"Bearer {os.getenv('RETELL_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Following the documentation structure
        payload = {
            "s2s_model": llm_config.get("s2s_model", "gpt-4o-realtime"),
            "model_temperature": llm_config.get("model_temperature", 0.7),
        }
        
        # Optional OpenAI API key
        if "openai_api_key" in llm_config:
            payload["openai_api_key"] = llm_config["openai_api_key"]
        
        # Optional system message
        if "system_message" in llm_config:
            payload["system_message"] = llm_config["system_message"]
            
        response = requests.post(url, json=payload, headers=headers)
        print(f"Retell LLM creation response: {response.status_code}, {response.text}")
        return response.json(), response.status_code

    @staticmethod
    def create_retell_agent(agent_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Create a Retell agent with existing LLM configuration"""
        retell_base_url = os.getenv("RETELL_BASE_URL", "https://api.retellai.com/v2")
        url = f"{retell_base_url}/create-agent"
        headers = {
            "Authorization": f"Bearer {os.getenv('RETELL_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Following documented structure for agent creation
        payload = {
            "agent_name": agent_data.get("name", "My Agent"),
            "response_engine": {
                "type": "retell-llm",
                # "llm_id": agent_data["llm_id"] | "llm_825113ca48f35f38e77b31efae9a",
                "llm_id":  "llm_825113ca48f35f38e77b31efae9a",
                "version": agent_data.get("llm_version", 0)
            },
            "voice_id": agent_data.get("voice_id", "11labs-michael"),
            "language": agent_data.get("language", "en-US"),
        }
        
        # Optional fields based on documentation
        if "initial_message" in agent_data:
            payload["initial_message"] = agent_data["initial_message"]
        
        if "webhook_url" in agent_data:
            payload["webhook_url"] = agent_data["webhook_url"]
            
        if "webhook_auth" in agent_data:
            payload["webhook_auth"] = agent_data["webhook_auth"]
            
        response = requests.post(url, json=payload, headers=headers)
        print(f"Retell agent creation response: {response.status_code}, {response.text}")
        return response.json(), response.status_code

    @staticmethod
    def create_retell_agent_with_llm(agent_config: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Complete flow: Create LLM then create agent"""
        # Prepare LLM configuration from agent config
        llm_config = {
            "s2s_model": agent_config.get("s2s_model", "gpt-4o-realtime"),
            "model_temperature": agent_config.get("temperature", 0.7),
        }
        
        # Add optional LLM parameters if provided
        if "system_message" in agent_config:
            llm_config["system_message"] = agent_config["system_message"]
        
        if "openai_api_key" in agent_config:
            llm_config["openai_api_key"] = agent_config["openai_api_key"]
        
        # Create the LLM
        llm_response, status = AgentCreator.create_retell_llm(llm_config)
        if status != 200:
            return llm_response, status
        
        print(f"LLM created successfully: {llm_response}")
        
        # Prepare agent data using the LLM ID
        agent_data = {
            "name": agent_config.get("name", "My Agent"),
            "voice_id": agent_config.get("voice_id", "11labs-michael"),
            "language": agent_config.get("language", "en-US"),
            # "llm_id": llm_response.get("llm_id"),
            "llm_id": "llm_825113ca48f35f38e77b31efae9a",
            "llm_version": llm_response.get("version", 0)
        }
        
        # Add optional agent parameters if provided
        if "initial_message" in agent_config:
            agent_data["initial_message"] = agent_config["initial_message"]
        elif "first_message" in agent_config:  # Support alternative naming
            agent_data["initial_message"] = agent_config["first_message"]
            
        if "webhook_url" in agent_config:
            agent_data["webhook_url"] = agent_config["webhook_url"]
            
        if "webhook_auth" in agent_config:
            agent_data["webhook_auth"] = agent_config["webhook_auth"]
        
        # Create the agent with the LLM ID
        return AgentCreator.create_retell_agent(agent_data)