.PHONY: dev
dev:
	./setup.sh

.PHONY: up
up:
	docker-compose up -d
	make ps

.PHONY: down
down:
	docker-compose down
	make ps

.PHONY: ps
ps:
	docker-compose ps

.PHONY: bash
bash:
	docker-compose run --rm app bash

.PHONY: shell
shell:
	docker-compose run --rm app ./manage.py shell_plus --ipython

.PHONY: migrations
migrations:
	docker-compose run --rm app ./manage.py makemigrations

.PHONY: migrate
migrate:
	docker-compose run --rm app ./manage.py migrate

.PHONY: etl
migrate:
	docker-compose run --rm app ./manage.py etl
