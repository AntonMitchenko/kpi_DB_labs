FROM postgres:15

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копирование init.sql в контейнер
COPY init.sql /docker-entrypoint-initdb.d/

# Изменение порта на 5432
EXPOSE 5432

# Конфигурация healthcheck
HEALTHCHECK --interval=5s --timeout=3s \
    CMD pg_isready -h localhost -U myuser -d mydb -p 5432 || exit 1

CMD ["postgres", "-p", "5432"]
