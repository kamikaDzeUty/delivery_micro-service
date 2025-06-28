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
        description="""
        ## Delivery Service API
        
        Микросервис для управления доставкой посылок.
        
        ### Основные возможности:
        - Создание и управление посылками
        - Автоматический расчет стоимости доставки
        - Асинхронная обработка через Celery
        - Валидация данных и логирование
        
        ### Endpoints:
        - `GET /health` - проверка состояния сервиса
        - `GET /docs` - Swagger документация
        - `GET /redoc` - ReDoc документация
        """,
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
        logger.info("Health check requested")
        return {
            "status": "healthy", 
            "service": "delivery-service",
            "version": "0.1.0"
        }
    
    # Include routers
    app.include_router(package_types_router)
    app.include_router(packages_router)
    
    logger.info("Application created successfully")
    return app

app = create_app()

# Логируем запуск приложения
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Delivery Service starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Delivery Service shutting down...")
