FROM python:3.9

# Устанавливаем рабочую директорию внутри контейнера

RUN mkdir /Lab3_Consumer
WORKDIR /Lab3_Consumer

# Копируем requirements.txt в контейнер
COPY requirements.txt /Lab3_Consumer/

# Устанавливаем зависимости приложения
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения в контейнер
COPY . /Lab3_Consumer/

EXPOSE 5000

# Определяем команду для запуска приложения
CMD ["python", "app.py"]