# src/delivery_service/main.py

from fastapi import FastAPI
from src.delivery_service.api.package_types import router as package_types_router
from src.delivery_service.api.packages      import router as packages_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Delivery Service",
        version="0.1.0",
        description="Микросервис для регистрации посылок и расчёта стоимости доставки",
    )
    # Подключаем роутеры из папки api/
    app.include_router(package_types_router)
    app.include_router(packages_router)
    return app

# этот объект и будет искаться по пути delivery_service.main:app
app = create_app()
