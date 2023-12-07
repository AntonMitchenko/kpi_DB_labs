FROM python:3.9

# Устанавливаем рабочую директорию внутри контейнера

RUN mkdir /Lab2_Worker
WORKDIR /Lab2_Worker

# Копируем requirements.txt в контейнер
COPY requirements.txt /Lab2_Worker/

# Устанавливаем зависимости приложения
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения в контейнер
COPY . /Lab2_Worker/

# Определяем команду для запуска приложения
CMD ["python", "app.py"]