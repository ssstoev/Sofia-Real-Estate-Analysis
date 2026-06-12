'''Orchestrate the API endpoints from this file'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.search_service import router as search_router
from api.chat import router as chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(chat_router)
