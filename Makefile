SHELL := /bin/bash # Use bash syntax
ARG := $(word 2, $(MAKECMDGOALS) )

black:
	black .

run:
	python ./backend/manage.py runserver
	cd ./frontend && npm start

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
