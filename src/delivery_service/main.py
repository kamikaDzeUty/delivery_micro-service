from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.delivery_service.api.package_types import router as package_types_router
from src.delivery_service.api.packages import router as packages_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Delivery Service",
        version="0.1.0",
        description="Микросервис для регистрации посылок и расчёта стоимости доставки",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "delivery-service"}
    
    # Include routers
    app.include_router(package_types_router)
    app.include_router(packages_router)
    
    return app

app = create_app()
