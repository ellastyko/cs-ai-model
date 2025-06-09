# Установка Python 3.13.4 (требует sudo)
install-python:
	# Для Ubuntu/WSL
	sudo apt update && sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget
	wget https://www.python.org/ftp/python/3.13.4/Python-3.13.4.tar.xz
	tar -xf Python-3.13.4.tar.xz
	cd Python-3.13.4 && ./configure --enable-optimizations && make -j$(nproc) && sudo make altinstall
	python3.13 --version

# Создание виртуального окружения и установка зависимостей
setup:
	python3.13 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "✅ Виртуальное окружение готово. Активируйте его:"
	@echo "source .venv/bin/activate  # Linux/macOS"
	@echo ".venv\\Scripts\\activate  # Windows"

# Запуск проекта (после активации .venv)
run:
	python3 main.py

# Очистка кеша и временных файлов
clean:
	rm -rf __pycache__ .pytest_cache
	find . -name "*.pyc" -delete

.PHONY: install-python setup run clean