from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.auth import router as auth_router
from app.routers.custom_meals import router as custom_meals_router
from app.routers.dashboard import router as dashboard_router
from app.routers.foods import router as foods_router
from app.routers.ingredients import router as ingredients_router
from app.routers.logs import router as logs_router
from app.routers.meals import router as meals_router
from app.routers.profile import router as profile_router
from app.routers.recommendations import router as recommendations_router

app = FastAPI(title=settings.project_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(foods_router)
app.include_router(ingredients_router)
app.include_router(logs_router)
app.include_router(custom_meals_router)
app.include_router(meals_router)
app.include_router(profile_router)
app.include_router(recommendations_router)


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
