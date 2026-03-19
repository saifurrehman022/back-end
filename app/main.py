from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.rag.routes import router as rag_router
from app.logging_config import setup_logging

setup_logging()

app = FastAPI(title="GrokRAG API", description="SaaS RAG Chat with Groq", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://echoloft-ai.vercel.app", 
                  ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(rag_router, prefix="/rag")

@app.get("/")
async def root():
    return {"message": "Welcome to GrokRAG API"}
