"""
Financial analysis API.

This module provides a simple API interface to the financial analysis workflow.
"""

import os
import sys
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()

# Import our workflow
from src.workflow.financial_analysis_flow import FinancialAnalysisWorkflow
from src.data_integration.financial_dataset_loader import FinancialDatasetLoader
from src.utils.auth import get_api_key
from src.utils.cache import InMemoryCache, DynamicTTLCache, RedisCache, FileCache
from src.prompts.financial_prompts import FinancialPrompts, model  # Import the Gemini model implementation

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize components
dataset_loader = FinancialDatasetLoader()
# Using the Gemini model instead of OpenAI
SELECTED_MODEL = os.getenv("SELECTED_MODEL", "gemini")
workflow = FinancialAnalysisWorkflow(model=SELECTED_MODEL)

# Initialize caching system
CACHE_TYPE = os.getenv("CACHE_TYPE", "file").lower()  # Default to file cache for stability
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default 1 hour
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Global in-memory cache as fallback
_memory_cache = {}

try:
    if CACHE_TYPE == "redis":
        logger.info(f"Initializing Redis cache at {REDIS_HOST}:{REDIS_PORT}")
        try:
            base_cache = RedisCache(
                redis_host=REDIS_HOST,
                redis_port=REDIS_PORT,
                redis_db=REDIS_DB,
                redis_password=REDIS_PASSWORD
            )
        except Exception as redis_error:
            logger.warning(f"Failed to initialize Redis cache: {str(redis_error)}. Falling back to file cache.")
            CACHE_TYPE = "file"
            base_cache = FileCache(cache_dir=CACHE_DIR, default_ttl=CACHE_TTL)
    elif CACHE_TYPE == "file":
        logger.info(f"Initializing file cache in directory: {CACHE_DIR}")
        base_cache = FileCache(cache_dir=CACHE_DIR, default_ttl=CACHE_TTL)
    else:
        logger.info("Initializing in-memory cache")
        CACHE_TYPE = "memory"
        base_cache = InMemoryCache(default_ttl=CACHE_TTL)
        
    # Wrap with dynamic TTL based on market volatility
    cache = DynamicTTLCache(
        base_cache=base_cache,
        volatility_evaluator=lambda: workflow.retriever.get_market_context().get("volatility", 0.5) if hasattr(workflow, 'retriever') else 0.5,
        high_volatility_threshold=1.5,
        low_volatility_ttl=CACHE_TTL,
        high_volatility_ttl=int(CACHE_TTL / 12)  # Much shorter TTL during high volatility
    )
    
    logger.info(f"Response caching initialized with type: {CACHE_TYPE}, default TTL: {CACHE_TTL}s")
    
except Exception as e:
    logger.warning(f"Failed to initialize cache: {str(e)}. Falling back to in-memory cache.")
    CACHE_TYPE = "memory"
    cache = InMemoryCache(default_ttl=CACHE_TTL)

# Initialize FastAPI
app = FastAPI(
    title="Financial Analysis API",
    description="API for analyzing financial data using Gemini and LangGraph",
    version="0.1.0"
)

# API Models
class AnalysisRequest(BaseModel):
    """Model for financial analysis request."""
    query: str
    dataset_name: Optional[str] = None
    dataset_type: Optional[str] = None

class AnalysisResponse(BaseModel):
    """Model for financial analysis response."""
    query: str
    analysis: str
    data_info: Dict[str, Any]
    market_context: Dict[str, Any]
    error: Optional[str] = None
    cached: bool = False

class DatasetInfo(BaseModel):
    """Model for dataset information."""
    name: str
    path: str
    type: str
    format: str
    size_mb: float

class CacheClearResponse(BaseModel):
    """Model for cache clear response."""
    status: str
    message: str

class CacheStatusResponse(BaseModel):
    """Model for cache status response."""
    cache_type: str
    entry_count: Any
    default_ttl: int
    is_dynamic_ttl: bool = True
    high_volatility_threshold: float = 1.5
    low_volatility_ttl: int = 3600
    high_volatility_ttl: int = 300

# Simple fallback caching mechanism
def generate_key(query):
    """Generate a simple hash key for caching."""
    return hashlib.md5(query.encode('utf-8')).hexdigest()

def cache_get(key):
    """Get from fallback cache."""
    if key in _memory_cache:
        entry = _memory_cache[key]
        if time.time() < entry['expires']:
            return entry['data']
    return None

def cache_set(key, data, ttl=3600):
    """Set in fallback cache."""
    _memory_cache[key] = {
        'data': data,
        'expires': time.time() + ttl
    }

def cache_clear():
    """Clear fallback cache."""
    _memory_cache.clear()

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their processing time."""
    start_time = time.time()
    
    # Get client IP and request details
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    url = request.url.path
    
    logger.info(f"Request received: {method} {url} from {client_host}")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate and log processing time
    process_time = time.time() - start_time
    logger.info(f"Request completed: {method} {url} - Status: {response.status_code} - Time: {process_time:.2f}s")
    
    return response

# API Routes
@app.get("/")
async def root():
    """API root endpoint."""
    endpoints = [
        "/",
        "/analyze",
        "/datasets",
        "/market_conditions",
        "/dataset/{dataset_name}/info",
        "/cache/clear",
        "/cache/status",
        "/debug/cache"
    ]
    
    return {
        "message": "Financial Analysis API",
        "version": "0.1.0",
        "model": SELECTED_MODEL,
        "cache_type": CACHE_TYPE,
        "endpoints": endpoints
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_financial_data(request: AnalysisRequest, api_key: str = Depends(get_api_key)):
    """
    Analyze financial data based on the provided query.
    
    Args:
        request: Analysis request with query and optional dataset info
        api_key: Validated API key
        
    Returns:
        Analysis response with results
    """
    try:
        # Generate a simpler cache key first
        simple_key = generate_key(request.query)
        logger.debug(f"Generated simple cache key: {simple_key} for query: {request.query}")
        
        # Try direct simple caching first
        cached_data = cache_get(simple_key)
        if cached_data:
            logger.info(f"Simple cache hit for query: {request.query[:30]}...")
            # Create a new response with cached=True flag
            cached_data['cached'] = True
            return AnalysisResponse(**cached_data)
            
        # Also try the more complex cache system
        try:
            # Generate cache key from request
            cache_key = cache.generate_cache_key(
                query=request.query,
                dataset_name=request.dataset_name,
                dataset_type=request.dataset_type
            )
            
            logger.debug(f"Generated cache key: {cache_key} for query: {request.query}")
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for key: {cache_key}, query: {request.query[:30]}...")
                # Create a new response with cached=True flag
                response = {
                    **cached_result,
                    "cached": True
                }
                return AnalysisResponse(**response)
        except Exception as cache_error:
            logger.warning(f"Error checking cache: {str(cache_error)}")
            
        logger.info(f"Cache miss for query: {request.query[:30]}...")
        
        # Check if we should use direct Gemini implementation instead of the workflow
        if SELECTED_MODEL == "gemini":
            # Get market context to add to the prompt
            market_context = workflow.retriever.get_market_context() if hasattr(workflow, 'retriever') else {}
            
            # Create a financial analysis prompt using the FinancialPrompts class
            financial_prompt = FinancialPrompts.get_analysis_prompt(
                query=request.query,
                context=f"Dataset: {request.dataset_name or 'Not specified'}, Type: {request.dataset_type or 'Not specified'}",
                market_conditions=market_context
            )
            
            # Execute the analysis using the Gemini model directly
            gemini_result = FinancialPrompts.analyze_financial_data(financial_prompt)
            
            # Prepare response
            response_data = {
                "query": request.query,
                "analysis": gemini_result.get("analysis", "No analysis generated."),
                "data_info": {
                    "dataset_name": request.dataset_name,
                    "dataset_type": request.dataset_type,
                    "model_used": gemini_result.get("model_used", "unknown")
                },
                "market_context": market_context,
                "error": gemini_result.get("error"),
                "cached": False
            }
        else:
            # Execute the original workflow
            result = workflow.execute(
                query=request.query,
                dataset_name=request.dataset_name,
                dataset_type=request.dataset_type
            )
            
            # Get market context
            market_context = result.get("market_context", {})
            
            # Prepare response
            response_data = {
                "query": request.query,
                "analysis": result.get("analysis_result", "No analysis generated."),
                "data_info": {
                    "dataset_name": request.dataset_name,
                    "dataset_type": request.dataset_type,
                    "num_records": result.get("data", {}).get("num_records", 0),
                    "columns": result.get("data", {}).get("columns", [])
                },
                "market_context": market_context,
                "error": result.get("error"),
                "cached": False
            }
        
        # Cache the result
        cache_data = {k: v for k, v in response_data.items() if k != "cached"}
        
        # Try both caching mechanisms
        try:
            # Store in simple cache
            logger.debug(f"Caching response with simple key: {simple_key}")
            cache_set(simple_key, cache_data)
            
            # Try complex cache too
            logger.debug(f"Caching response with key: {cache_key}")
            cache.set(cache_key, cache_data)
        except Exception as cache_error:
            logger.warning(f"Error caching response: {str(cache_error)}")
        
        return AnalysisResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/datasets", response_model=List[DatasetInfo])
async def list_datasets():
    """
    List all available financial datasets.
    
    Returns:
        List of dataset information
    """
    try:
        datasets = dataset_loader.list_available_datasets()
        return datasets
        
    except Exception as e:
        logger.error(f"Error in datasets endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")

@app.get("/market_conditions")
async def get_market_conditions():
    """
    Get current market conditions including volatility.
    
    Returns:
        Market conditions information
    """
    try:
        market_context = workflow.retriever.get_market_context()
        return market_context
        
    except Exception as e:
        logger.error(f"Error in market_conditions endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get market conditions: {str(e)}")

@app.get("/dataset/{dataset_name}/info")
async def get_dataset_info(dataset_name: str):
    """
    Get information about a specific dataset.
    
    Args:
        dataset_name: Name of the dataset
        
    Returns:
        Dataset information
    """
    try:
        # Find dataset in the available datasets
        datasets = dataset_loader.list_available_datasets()
        dataset_info = next((d for d in datasets if d["name"] == dataset_name), None)
        
        if not dataset_info:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found")
        
        return dataset_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dataset info endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dataset info: {str(e)}")

@app.post("/cache/clear", response_model=CacheClearResponse)
async def clear_cache_endpoint(api_key: str = Depends(get_api_key)):
    """
    Clear the response cache.
    
    Args:
        api_key: Validated API key
        
    Returns:
        Status message
    """
    try:
        logger.info("Clearing cache")
        # Clear both caching mechanisms
        cache_clear()
        
        try:
            cache.clear()
        except Exception as e:
            logger.warning(f"Error clearing complex cache: {str(e)}")
            
        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/cache/status", response_model=CacheStatusResponse)
async def cache_status_endpoint(api_key: str = Depends(get_api_key)):
    """
    Get the status of the cache.
    
    Returns:
        Cache status information
    """
    try:
        logger.info("Getting cache status")
        # Get basic cache info
        status = {
            "cache_type": CACHE_TYPE,
            "entry_count": len(_memory_cache),
            "default_ttl": CACHE_TTL,
            "is_dynamic_ttl": True,
            "high_volatility_threshold": getattr(cache, "high_volatility_threshold", 1.5),
            "low_volatility_ttl": getattr(cache, "low_volatility_ttl", CACHE_TTL),
            "high_volatility_ttl": getattr(cache, "high_volatility_ttl", int(CACHE_TTL / 12))
        }
        
        # Add more detailed info based on cache type
        try:
            # For FileCache, get more detailed stats
            if isinstance(cache.base_cache, FileCache):
                # Count current entries
                try:
                    import glob
                    cache_files = glob.glob(os.path.join(cache.base_cache.cache_dir, "*.json"))
                    status["file_entry_count"] = len(cache_files)
                    status["cache_dir"] = cache.base_cache.cache_dir
                except Exception as e:
                    logger.warning(f"Error getting file cache stats: {str(e)}")
                    
            # For InMemoryCache
            elif isinstance(cache.base_cache, InMemoryCache):
                status["memory_entry_count"] = len(cache.base_cache._cache)
                
            # For RedisCache
            elif hasattr(cache.base_cache, 'redis') and cache.base_cache.redis:
                try:
                    info = cache.base_cache.redis.info()
                    status["redis_entry_count"] = cache.base_cache.redis.dbsize()
                    status["redis_used_memory"] = info.get("used_memory_human")
                except Exception as e:
                    logger.warning(f"Error getting Redis stats: {str(e)}")
        except Exception as e:
            logger.warning(f"Error getting detailed cache stats: {str(e)}")
            
        return status
            
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        return {"cache_type": "unknown", "entry_count": 0, "default_ttl": 0, 
                "is_dynamic_ttl": False, "high_volatility_threshold": 0, 
                "low_volatility_ttl": 0, "high_volatility_ttl": 0}

@app.get("/debug/cache")
async def debug_cache(api_key: str = Depends(get_api_key)):
    """
    Debug endpoint to inspect current cache state.
    
    Args:
        api_key: Validated API key
        
    Returns:
        Cache debug information
    """
    try:
        # Generate debug info based on cache type
        if isinstance(cache.base_cache, InMemoryCache):
            # For InMemoryCache, we can directly access the cache and expiry dicts
            cache_contents = {}
            for key, value in cache.base_cache._cache.items():
                expiry_time = cache.base_cache._expiry.get(key, 0)
                time_left = max(0, expiry_time - time.time())
                cache_contents[key] = {
                    "expires_in": f"{time_left:.2f} seconds",
                    "value_preview": str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                }
            
            return {
                "cache_type": CACHE_TYPE,
                "cache_entries": len(cache.base_cache._cache),
                "contents": cache_contents
            }
        elif CACHE_TYPE == "redis":
            # For Redis, get all keys with our prefix
            keys = cache.base_cache.redis.keys(f"{cache.base_cache.key_prefix}*")
            contents = {}
            
            for key in keys:
                # Get TTL for this key
                ttl = cache.base_cache.redis.ttl(key)
                
                # Get a preview of the value
                value = cache.base_cache.redis.get(key)
                value_preview = value[:100] + "..." if value and len(value) > 100 else value
                
                contents[key] = {
                    "expires_in": f"{ttl} seconds" if ttl > 0 else "expired",
                    "value_preview": value_preview
                }
            
            return {
                "cache_type": CACHE_TYPE,
                "cache_entries": len(keys),
                "contents": contents
            }
        else:
            return {
                "cache_type": CACHE_TYPE,
                "error": "Cannot inspect this cache type"
            }
    except Exception as e:
        logger.error(f"Error in debug cache endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to debug cache: {str(e)}")

# Log all available endpoints at startup
@app.on_event("startup")
async def startup_event():
    """Log all available endpoints at startup."""
    logger.info("API starting up")
    logger.info(f"Registered endpoints:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ", ".join(route.methods)
            logger.info(f"  {methods} {route.path}")

# Run the API (for local development)
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server")
    uvicorn.run(app, host="0.0.0.0", port=8000) 