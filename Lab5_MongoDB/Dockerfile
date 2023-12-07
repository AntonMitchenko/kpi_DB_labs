FROM python:3.9

# Устанавливаем рабочую директорию внутри контейнера

RUN mkdir /app
WORKDIR /app

# Копируем requirements.txt в контейнер
COPY requirements.txt /app/

# Устанавливаем зависимости приложения
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения в контейнер
COPY . /app/

# Определяем команду для запуска приложения
CMD ["python", "app.py"]