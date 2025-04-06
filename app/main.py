from typing import Dict
from fastapi import FastAPI
from app.controllers.upload import router as upload_router
from dotenv import load_dotenv



load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="ResQ AI Server",
    description="A basic FastAPI application",
    version="0.1.0",
)


app = FastAPI()


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a simple greeting message.

    Returns:
        Dict[str, str]: A dictionary with a welcome message
    """
    return {"message": "Hello World"}


app.include_router(upload_router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
