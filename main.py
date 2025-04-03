from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import asyncio
import uuid
import os
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, HttpUrl
import json
from datetime import datetime
import logging
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DeepCrawlStrategy,
    DeepCrawlConfig
)

# ====== Logger Setup ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("crawl4ai-api")

# ====== Models ======
class CrawlRequest(BaseModel):
    url: str = Field(..., description="URL to crawl")
    depth: int = Field(0, description="Depth of crawling (0 for single page)")
    max_pages: int = Field(10, description="Maximum number of pages to crawl in deep crawl mode")
    strategy: str = Field("bfs", description="Strategy for deep crawling: bfs, dfs, or bestfirst")
    headless: bool = Field(True, description="Run browser in headless mode")
    extract_images: bool = Field(False, description="Extract images from the page")
    extract_links: bool = Field(True, description="Extract links from the page")
    user_query: Optional[str] = Field(None, description="User query for focused crawling")
    
class CrawlResponse(BaseModel):
    task_id: str
    status: str = "pending"
    created_at: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    
class CrawlResult(BaseModel):
    task_id: str
    status: str
    url: str
    markdown: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

# ====== API Setup ======
app = FastAPI(
    title="Crawl4AI API",
    description="API for crawling websites using Crawl4AI",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key auth
API_KEY = os.environ.get("API_KEY", "development-key")

def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return True

# In-memory task storage (replace with a database in production)
tasks: Dict[str, Dict[str, Any]] = {}

# ====== Crawling Function ======
async def crawl_website(task_id: str, request: CrawlRequest):
    try:
        logger.info(f"Starting crawl task {task_id} for URL: {request.url}")
        
        # Update task status
        tasks[task_id]["status"] = "running"
        
        # Configure browser
        browser_config = BrowserConfig(
            headless=request.headless,
            verbose=True,
        )
        
        # Configure deep crawl if depth > 0
        deep_crawl_config = None
        if request.depth > 0:
            deep_crawl_config = DeepCrawlConfig(
                strategy=request.strategy,
                max_pages=request.max_pages,
                max_depth=request.depth,
                user_query=request.user_query
            )
        
        # Configure crawler run
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            deep_crawl_config=deep_crawl_config,
            extract_links=request.extract_links,
            extract_images=request.extract_images,
        )
        
        # Run the crawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=request.url,
                config=run_config
            )
        
        # Process and store results
        tasks[task_id].update({
            "status": "completed",
            "result": {
                "markdown": result.markdown.fit_markdown if result.markdown else None,
                "links": result.links if hasattr(result, 'links') and result.links else None,
                "images": result.images if hasattr(result, 'images') and result.images else None,
            },
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"Completed crawl task {task_id}")
        
    except Exception as e:
        logger.error(f"Error in crawl task {task_id}: {str(e)}")
        tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

# ====== API Endpoints ======
@app.post("/api/crawl", response_model=CrawlResponse, dependencies=[Depends(verify_api_key)])
async def create_crawl_task(request: CrawlRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "url": request.url,
        "created_at": created_at,
        "request": request.dict()
    }
    
    background_tasks.add_task(crawl_website, task_id, request)
    
    return CrawlResponse(
        task_id=task_id,
        status="pending",
        created_at=created_at
    )

@app.get("/api/task/{task_id}", response_model=TaskStatus, dependencies=[Depends(verify_api_key)])
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )

@app.get("/api/result/{task_id}", response_model=CrawlResult, dependencies=[Depends(verify_api_key)])
async def get_crawl_result(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Task not yet completed")
    
    result = task.get("result", {})
    
    return CrawlResult(
        task_id=task_id,
        status=task["status"],
        url=task["url"],
        markdown=result.get("markdown"),
        links=result.get("links"),
        images=result.get("images"),
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "crawl4ai-api"}

@app.get("/")
async def root():
    return {
        "service": "Crawl4AI API",
        "status": "running",
        "endpoints": [
            {"path": "/api/crawl", "method": "POST", "description": "Start a new crawl task"},
            {"path": "/api/task/{task_id}", "method": "GET", "description": "Check task status"},
            {"path": "/api/result/{task_id}", "method": "GET", "description": "Get task results"},
            {"path": "/api/health", "method": "GET", "description": "Service health check"}
        ]
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
