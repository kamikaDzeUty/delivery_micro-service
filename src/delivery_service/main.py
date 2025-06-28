from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.delivery_service.api.package_types import router as package_types_router
from src.delivery_service.api.packages import router as packages_router
from src.delivery_service.core.logging import setup_logging, RequestLoggingMiddleware, get_logger

# Настраиваем логирование
setup_logging()
logger = get_logger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Delivery Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Добавляем middleware для логирования запросов
    app.add_middleware(RequestLoggingMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Vue dev server
            "https://your-frontend-domain.com",  # Production frontend
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        logger.info("Запрос проверки состояния сервиса")
        return {
            "status": "healthy", 
            "service": "delivery-service",
            "version": "0.1.0"
        }
    
    # Include routers
    app.include_router(package_types_router)
    app.include_router(packages_router)
    
    logger.info("Приложение успешно создано")
    return app

app = create_app()

@asynccontextmanager
async def lifespan():
    logger.info("🚀 Сервис доставки запускается...")
    yield
    logger.info("🛑 Сервис доставки завершает работу...")
