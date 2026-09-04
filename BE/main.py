from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from BE.config.settings import BASE_DIR
from BE.routers.auth_router import router as auth_router
from BE.routers.conversation_router import router as conversation_router
from BE.routers.message_router import lazy_router as lazy_message_router
from BE.routers.message_router import router as message_router
from BE.routers.read_status_router import router as read_status_router
from BE.routers.user_router import router as user_router
from BE.websocket.router import router as websocket_router
origins = [
    "http://localhost:5173",  # Vite dev server
]
app = FastAPI(title="Chat System API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static", check_dir=False), name="static")
app.include_router(auth_router)
app.include_router(conversation_router)
app.include_router(message_router)
app.include_router(lazy_message_router)
app.include_router(read_status_router)
app.include_router(user_router)
app.include_router(websocket_router)
