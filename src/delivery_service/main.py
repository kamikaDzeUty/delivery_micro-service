from fastapi import FastAPI
from src.delivery_service.api.package_types import router as package_types_router
from src.delivery_service.api.packages      import router as packages_router

def create_app() -> FastAPI:
    App = FastAPI(
        title="Delivery Service",
        version="0.1.0",
        description="Микросервис для регистрации посылок и расчёта стоимости доставки",
    )
    App.include_router(package_types_router)
    App.include_router(packages_router)
    return App

app = create_app()
