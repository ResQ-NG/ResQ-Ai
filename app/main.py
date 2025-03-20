"""
Main FastAPI application module.
"""
from typing import Dict

from fastapi import FastAPI

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Application",
    description="A basic FastAPI application",
    version="0.1.0"
)


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a simple greeting message.
    
    Returns:
        Dict[str, str]: A dictionary with a welcome message
    """
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

