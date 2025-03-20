# Makefile for Project Maintenance

PROJECT_DIR=./app
TEST_DIR=./tests
APP_MODULE=app.main:app

lint:
	ruff check $(PROJECT_DIR)

fix:
	ruff check $(PROJECT_DIR) --fix

format:
	black $(PROJECT_DIR)

style:
	make format
	make fix

install:
	pip install -r requirements.txt

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

run:
	ENV=dev uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

setup_venv:
	python3 -m venv venv && make shell

setup_db:
	PYTHONPATH=. python3 db/setup_db.py

# Below is my attempt for extra polish with some ASCII art style docs ;) 
shell:
	@exec zsh -c "\
	source venv/bin/activate && \
	echo -e '\n\
	||============================================================||\n\
	||  Virtual environment activated.                            ||\n\
	||  Type \"exit\" or \"deactivate\" to deactivate.            ||\n\
	||============================================================||\n\
	\n\
	||------------------------------------------------------------||\n\
	||  Run \"make install\" to install dependencies                ||\n\
	||  Run \"make help\" for further commands                      ||\n\
	||------------------------------------------------------------||\n' && \
	exec zsh"

freeze:
	pip freeze > requirements.txt

test:
	pytest $(TEST_DIR) --cov=$(PROJECT_DIR) --cov-report=term-missing

help:
	@echo "Available commands:"
	@echo "  make lint        - Check code with Ruff"
	@echo "  make fix         - Run Ruff with auto-fix"
	@echo "  make format      - Format code with Black"
	@echo "  make style       - Run Black and Ruff with fix"
	@echo "  make install     - Install dependencies from requirements.txt"
	@echo "  make clean       - Remove Python cache files"
	@echo "  make run         - Run the main application with Uvicorn"
	@echo "  make setup_venv  - Set up the virtual environment"
	@echo "  make shell       - Activate the virtual environment with a message"
	@echo "  make freeze      - Freeze current dependencies to requirements.txt"
	@echo "  make test        - Run tests with pytest"
	@echo "  make setup_db    - Sets up the database tables"