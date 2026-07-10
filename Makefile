SHELL := /bin/bash # Use bash syntax
ARG := $(word 2, $(MAKECMDGOALS) )
BACK_ENV ?= ./backend/pizza_simulator/.env

format:
	black .
	cd ./frontend && npm run format

run-be:
	python ./backend/manage.py runserver

run-fe:
	cd ./frontend && npm start

run:
	make run-be & make run-fe

stop-local: # pkill -f python # sudo lsof -i tcp:8000 # sudo lsof -t -i tcp:8000 | xargs kill -9
	taskkill /im python.exe /f

bash:
	docker exec -it backend_revenew-backend-1 /bin/bash

show_containers:
	docker container ls --format=$(FORMAT)

lab:
	python manage.py shell_plus --lab

query:
	python manage.py shell_plus

migrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

dev:
	uv pip install -r ./backend/requirements.txt
	cd ./frontend && npm install

up:
	docker compose up -d

down:
	docker compose down

build:
	docker build -t omp .
	make up

rebuild:
	docker stop omp && docker rm omp
	docker build --no-cache -t omp .
	make up

image-down:
	docker stop omp

remove:
	docker rm omp

image-up:
	docker run -d \
	-p 8000:8000 \
	--env-file $(BACK_ENV) \
	--name omp \
	omp

dev-tools:
	uv pip install --python .venv/bin/python -r ./backend/requirements-dev.txt
	cd ./frontend && npm install
	.venv/bin/pre-commit install

test:
	bash scripts/check-backend.sh
	bash scripts/check-frontend.sh

test-be:
	bash scripts/check-backend.sh

test-fe:
	bash scripts/check-frontend.sh

lint:
	.venv/bin/ruff check backend
	cd frontend && npm run lint

check: lint test
