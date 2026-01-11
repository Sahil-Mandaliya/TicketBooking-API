.PHONY: build up down test migrate migrations restart

build:
	docker-compose build

start:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart web

migrations:
	docker-compose exec web python manage.py makemigrations ticketing

migrate:
	docker-compose exec web python manage.py migrate

test:
	docker-compose exec web python manage.py test ticketing.tests

shell:
	docker-compose exec web python manage.py shell