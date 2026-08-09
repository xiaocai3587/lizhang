"""礼账 Lizhang 后端主程序"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import persons, events, gifts, relations, graph, stats, data


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="礼账 Lizhang", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(persons.router)
app.include_router(events.router)
app.include_router(gifts.router)
app.include_router(relations.router)
app.include_router(graph.router)
app.include_router(stats.router)
app.include_router(data.router)


@app.get("/")
def root():
    return {"app": "礼账 Lizhang", "version": "2.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
