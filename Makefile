APP_VERSION ?= v0.1.0
IMAGE_REGISTRY ?= quay.io/opstree
IMAGE_NAME ?= attendance-api

# Build employee binary
build: fmt
	poetry config virtualenvs.create false
	poetry install --no-root --no-interaction --no-ansi

# Run go fmt against code
fmt:
	pylint router/ client/ models/ utils/ app.py

docker-build:
	docker build -t ${IMAGE_REGISTRY}/${IMAGE_NAME}:${APP_VERSION} -f Dockerfile .

docker-push:
	docker push ${IMAGE_REGISTRY}/${IMAGE_NAME}:${APP_VERSION} 

LIQUIBASE_CLS = /home/ubuntu/attendance-api/liquibase_lib/postgresql-42.5.4.jar
CHANGELOG = migration/db-changelog.xml
JDBC_URL = jdbc:postgresql://127.0.0.1:5432/attendance_db
DB_USER = postgres
DB_PASS = password

run-migrations:
	@echo "Running liquibase migrations using $(CHANGELOG)"
	liquibase --changeLogFile=$(CHANGELOG) \
	  --url=$(JDBC_URL) \
	  --username=$(DB_USER) \
	  --password=$(DB_PASS) \
	  --driver=org.postgresql.Driver \
	  --classpath=$(LIQUIBASE_CLS) \
	  update

