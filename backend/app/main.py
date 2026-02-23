"""
ReadPulse backend — scalable, serverless-ready.
Add new routers in app/routers and mount here.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.routers import health, summarize

#auth (mount router) 
#new
from app.routers import auth
from app.db import init_db




app = FastAPI(
    title="ReadPulse",
    description="Human-like article summarization API",
    version="1.0.0",
)

cfg = get_config()
origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()] if cfg.cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Routers: add new feature routes here -----
app.include_router(health.router)
app.include_router(summarize.router)


#new
app.include_router(auth.router) 



#new
@app.on_event("startup")
def on_startup():
    init_db()

# Future: app.include_router(url_fetch.router, prefix="/api")    