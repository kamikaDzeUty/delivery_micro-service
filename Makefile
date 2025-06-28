# Makefile
COMPOSE = docker-compose
# По умолчанию подставится имя миграции, если вы не передадите MSG
MSG ?= "new migration"

.PHONY: help build up down ps logs db-up db-down \
        migrate-new migrate-up migrate-down

## build          — Собрать Docker-образ приложения
build:
	$(COMPOSE) build app

## up             — Поднять все сервисы в фоне
up:
	$(COMPOSE) up -d

## down           — Остановить и удалить все контейнеры
down:
	$(COMPOSE) down

## ps             — Показать статус контейнеров
ps:
	$(COMPOSE) ps

## logs           — Посмотреть логи всех сервисов (фоллоу)
logs:
	$(COMPOSE) logs -f

## db-up          — Поднять только сервис БД
db-up:
	$(COMPOSE) up -d db

## db-down        — Остановить только сервис БД
db-down:
	$(COMPOSE) stop db

## migrate-new    — Сгенерировать новую Alembic-миграцию
# Usage: make migrate-new MSG="create package_types table"
migrate-new:
	@echo "Generating new migration: $(MSG)"
	$(COMPOSE) run --rm app alembic revision --autogenerate -m "$(MSG)"

## migrate-up     — Применить все незакатанные миграции
migrate-up:
	@echo "Upgrading database to head"
	$(COMPOSE) run --rm app alembic upgrade head

## migrate-down   — Откатить последнюю миграцию
migrate-down:
	@echo "Downgrading database by one revision"
	$(COMPOSE) run --rm app alembic downgrade -1
