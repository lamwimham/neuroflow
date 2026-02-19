"""
NeuroFlow Web Console - Backend API Server

FastAPI-based backend for the web console.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import time
from datetime import datetime

app = FastAPI(title="NeuroFlow Web Console API", version="0.5.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data (in production, this would connect to actual NeuroFlow services)
AGENTS = [
    {
        "id": "agent-1",
        "name": "Research Agent",
        "description": "Specializes in web research and information gathering",
        "status": "active",
        "skills": ["web-search", "data-collection", "summarization"],
        "created_at": "2024-01-10T10:00:00Z",
    },
    {
        "id": "agent-2",
        "name": "Writer Agent",
        "description": "Specializes in content creation and writing",
        "status": "active",
        "skills": ["text-generation", "editing", "proofreading"],
        "created_at": "2024-01-12T14:30:00Z",
    },
    {
        "id": "agent-3",
        "name": "Data Analyst Agent",
        "description": "Specializes in data analysis and visualization",
        "status": "idle",
        "skills": ["data-analysis", "visualization", "statistics"],
        "created_at": "2024-01-15T09:15:00Z",
    },
]

SKILLS = [
    {"id": "web-search", "name": "Web Search", "description": "Search the web for information", "category": "Research", "version": "1.0.0", "installed": True},
    {"id": "data-analysis", "name": "Data Analysis", "description": "Analyze datasets", "category": "Analytics", "version": "1.2.0", "installed": True},
    {"id": "text-generation", "name": "Text Generation", "description": "Generate human-like text", "category": "NLP", "version": "2.0.0", "installed": True},
    {"id": "code-review", "name": "Code Review", "description": "Review and analyze code", "category": "Development", "version": "1.1.0", "installed": False},
    {"id": "image-recognition", "name": "Image Recognition", "description": "Recognize objects in images", "category": "CV", "version": "1.0.0", "installed": False},
]

METRICS = {
    "agents": {"active": 3, "total": 3},
    "skills": {"total": 12, "installed": 8},
    "requests": {"perMinute": 42, "total": 15234},
    "performance": {"avgLatency": 45, "p99Latency": 85},
}

# Models
class AgentCreate(BaseModel):
    name: str
    description: str
    skills: Optional[List[str]] = []

class AgentExecute(BaseModel):
    message: str

# Routes
@app.get("/")
async def root():
    return {"message": "NeuroFlow Web Console API", "version": "0.5.0"}

@app.get("/agents")
async def list_agents():
    return {"data": AGENTS}

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"data": agent}

@app.post("/agents")
async def create_agent(agent: AgentCreate):
    new_agent = {
        "id": f"agent-{len(AGENTS) + 1}",
        "name": agent.name,
        "description": agent.description,
        "status": "active",
        "skills": agent.skills or [],
        "created_at": datetime.now().isoformat(),
    }
    AGENTS.append(new_agent)
    return {"data": new_agent}

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    global AGENTS
    AGENTS = [a for a in AGENTS if a["id"] != agent_id]
    return {"message": "Agent deleted"}

@app.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, request: AgentExecute):
    # Simulate agent execution
    await asyncio.sleep(0.5)
    
    # Mock response
    response = f"I received your message: '{request.message}'. I'm a mock agent response."
    
    return {
        "result": response,
        "execution_time_ms": 123,
        "tokens_used": 45,
    }

@app.get("/skills")
async def list_skills():
    return {"data": SKILLS}

@app.get("/monitoring/metrics")
async def get_metrics():
    # Add some randomness to metrics
    import random
    metrics = METRICS.copy()
    metrics["requests"]["perMinute"] = random.randint(35, 50)
    metrics["performance"]["avgLatency"] = random.randint(40, 55)
    return {"data": metrics}

@app.get("/monitoring/logs")
async def get_logs(limit: int = 100):
    logs = []
    for i in range(limit):
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": f"Agent executed successfully {i}",
        })
    return {"data": logs}

@app.get("/mcp/servers")
async def list_mcp_servers():
    return {
        "data": [
            {"name": "filesystem", "connected": True, "tools": 3},
            {"name": "memory", "connected": True, "tools": 2},
            {"name": "terminal", "connected": True, "tools": 2},
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
