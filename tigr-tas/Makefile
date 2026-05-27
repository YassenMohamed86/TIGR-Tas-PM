.PHONY: up down restart logs build test migrate shell check

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

build:
	docker compose build

test:
	docker compose -f docker-compose.test.yml up -d db_test redis_test
	sleep 3
	docker compose exec -e APP_ENV=testing api pytest -v
	docker compose -f docker-compose.test.yml down

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

shell:
	docker compose exec api sh

psql:
	docker compose exec db psql -U tigr_user -d tigr_tas
