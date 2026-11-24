.PHONY: up down logs migrate revision shell-backend ps build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

migrate:
	docker compose exec backend alembic upgrade head

revision:
	docker compose exec backend alembic revision --autogenerate -m "$(m)"

shell-backend:
	docker compose exec backend bash

build:
	docker compose build
