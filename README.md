# airflow_superset_project

## Описание моей части проекта

В рамках первой части проекта была настроена серверная инфраструктура для хранения данных клиентов банка.

Что сделано:
- создана и подготовлена виртуальная машина Ubuntu;
- установлен Docker и Docker Compose;
- PostgreSQL 15 развернут в Docker-контейнере;
- создана база данных `bank_analytics`;
- исторический датасет клиентов загружен в таблицу `customers`;
- внешний доступ к PostgreSQL открыт через порт `5432`;
- подключение к базе данных извне проверено.

Эта часть проекта подготавливает источник данных для дальнейшей работы Airflow и Superset.

---

## Используемые файлы

- `docker-compose.yml` — конфигурация PostgreSQL в Docker
- `.env.example` — пример переменных окружения
- `.env` — рабочий файл с реальными параметрами подключения
- `credit_clients.csv` — датасет клиентов
- `README.md` — инструкция по запуску

---

## Предварительные требования

Перед запуском необходимо:
- создать виртуальную машину Ubuntu;
- иметь SSH-доступ к серверу;
- иметь CSV-файл с историческими данными клиентов;
- иметь доступ к GitHub-репозиторию проекта.

---

## 1. Подключение к серверу

Подключение по SSH:

```bash
ssh -i /path/to/key.pem ubuntu@<SERVER_PUBLIC_IP>

```
## 2. Установка Docker и Docker Compose

Обновление системы:
sudo apt update
sudo apt install -y ca-certificates curl

Добавление официального Docker repository:
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

Установка Docker:
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

Проверка:
docker --version
docker compose version

Добавление пользователя в группу Docker:
sudo usermod -aG docker $USER
newgrp docker

## 3. Подготовка рабочей директории

Создание структуры проекта:
mkdir -p ~/airflow_superset_project/{postgres/init,data,logs,backups}
cd ~/airflow_superset_project

## 4. Настройка переменных окружения

Создать файл .env на основе .env.example.

Пример содержимого:
POSTGRES_DB=bank_analytics
POSTGRES_USER=bank_admin
POSTGRES_PASSWORD=your_password_here
POSTGRES_PORT=5432
SUPERSET_PORT=8088

## 5. Настройка Docker Compose

Файл docker-compose.yml:

services:
  postgres:
    image: postgres:15
    container_name: bank_postgres
    restart: unless-stopped
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    networks:
      - bank_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

networks:
  bank_net:

volumes:
  postgres_data:

## 6. Запуск PostgreSQL

Запуск контейнера:
docker compose up -d

Проверка:
docker ps
docker compose logs -f postgres

Ожидаемый результат: контейнер bank_postgres находится в статусе Up или healthy, а в логах есть сообщение:

database system is ready to accept connections

## 7. Загрузка исторического датасета на сервер

Передать CSV-файл на сервер:

scp -i /path/to/key.pem credit_clients.csv ubuntu@<SERVER_PUBLIC_IP>:/home/ubuntu/airflow_superset_project/data/

Скопировать файл внутрь контейнера PostgreSQL:

docker cp ~/airflow_superset_project/data/credit_clients.csv bank_postgres:/tmp/credit_clients.csv

## 8. Создание таблицы и загрузка данных

Подключение к PostgreSQL:
docker exec -it bank_postgres psql -U bank_admin -d bank_analytics

Создание таблиц:
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS customers_stage;

CREATE TABLE customers (
    "Date" DATE,
    "CustomerId" BIGINT PRIMARY KEY,
    "Surname" TEXT,
    "CreditScore" INT,
    "Geography" TEXT,
    "Gender" TEXT,
    "Age" INT,
    "Tenure" INT,
    "Balance" NUMERIC(15,2),
    "NumOfProducts" INT,
    "HasCrCard" INT,
    "IsActiveMember" INT,
    "EstimatedSalary" NUMERIC(15,2),
    "Exited" INT
);

CREATE TABLE customers_stage (
    "Date" DATE,
    "CustomerId" BIGINT,
    "Surname" TEXT,
    "CreditScore" INT,
    "Geography" TEXT,
    "Gender" TEXT,
    "Age" INT,
    "Tenure" INT,
    "Balance" NUMERIC(15,2),
    "NumOfProducts" INT,
    "HasCrCard" INT,
    "IsActiveMember" INT,
    "EstimatedSalary" NUMERIC(15,2),
    "Exited" INT
);

Импорт CSV:
\copy customers_stage FROM '/tmp/credit_clients.csv' DELIMITER ',' CSV HEADER;

Перенос данных в основную таблицу:
INSERT INTO customers (
    "Date",
    "CustomerId",
    "Surname",
    "CreditScore",
    "Geography",
    "Gender",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
    "Exited"
)
SELECT
    "Date",
    "CustomerId",
    "Surname",
    "CreditScore",
    "Geography",
    "Gender",
    "Age",
    "Tenure",
    "Balance",
    "NumOfProducts",
    "HasCrCard",
    "IsActiveMember",
    "EstimatedSalary",
    "Exited"
FROM customers_stage
ON CONFLICT ("CustomerId") DO NOTHING;

Проверка:

SELECT COUNT(*) FROM customers;
SELECT * FROM customers LIMIT 5;

Ожидаемый результат: в таблице customers загружено 10000 строк.

Выход из PostgreSQL:
\q

## 9. Открытие внешнего доступа к PostgreSQL

В AWS Security Group необходимо добавить inbound rule:
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: IP команды или временно 0.0.0.0/0 для тестирования

Проверка с локальной машины:
nc -vz <SERVER_PUBLIC_IP> 5432

Ожидаемый результат:
Connection to <SERVER_PUBLIC_IP> 5432 port [tcp/postgresql] succeeded!

## 10. Параметры подключения к базе

Для подключения из Superset, Airflow, DBeaver или psql используются следующие параметры:

Host: <SERVER_PUBLIC_IP>
Port: 5432
Database: bank_analytics
User: bank_admin
Password: значение из .env

Основная таблица:
customers

Названия колонок сохранены как в исходном CSV:
Date
CustomerId
Surname
CreditScore
Geography
Gender
Age
Tenure
Balance
NumOfProducts
HasCrCard
IsActiveMember
EstimatedSalary
Exited

# 11. Настройка S3 для новых данных

Для последующей автоматической загрузки новых данных создан S3 bucket.

Подготовлено:
- создан bucket для хранения новых CSV-файлов;
- создан IAM user с ограниченным доступом к bucket;
- подготовлена папка `new_data/` для размещения новых файлов.

Параметры, которые передаются разработчику Airflow:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION=ca-central-1`
- `S3_BUCKET=<bucket_name>`
- `S3_PREFIX=new_data/`

Новые CSV-файлы должны загружаться в папку `new_data/` внутри bucket.


# 12. Apache Airflow
Архитектура
    • Оркестрация: Apache Airflow 2.7.0 (в Docker).
    • Хранилище данных: PostgreSQL 15.
    • Источник: AWS S3 Bucket (регион ca-central-1).
    • Визуализация: Apache Superset.

### Быстрый старт
12.1. Подготовка инфраструктуры
Если после запуска docker compose контейнеры не поднялись или возникли ошибки доступа к папкам, выполните создание каталогов и назначьте полные права:
Bash
##### Создание необходимых директорий
mkdir -p dags logs plugins data scripts

##### Назначение прав доступа (рекурсивно)
sudo chmod -R 777 dags logs plugins data scripts

12.2. Настройка безопасности (Fernet Key)
Для шифрования паролей в базе данных Airflow необходимо сгенерировать ключ и прописать его в файл .env:
Bash
##### Генерация ключа
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Скопируйте полученную строку и добавьте в .env: AIRFLOW__CORE__FERNET_KEY=ваш_ключ

12.3. Инициализация базы данных и Airflow
Выполните последовательно команды для создания БД и применения миграций Airflow:
Bash
##### Создание базы данных внутри контейнера Postgres
docker exec -it bank_postgres psql -U admin -c "CREATE DATABASE airflow_db;"

##### Инициализация структуры таблиц Airflow
docker exec -it bank_airflow_webserver airflow db init

12.4. Создание администратора Airflow
Создайте пользователя для входа в веб-интерфейс:
Bash
docker exec -it bank_airflow_webserver airflow users create \
    --username bank_admin \
    --firstname Stars25 \
    --lastname Engineer \
    --role Admin \
    --email admin@example.com \
    --password StrongPass123!

### Настройка подключений (Connections)
После входа в Airflow (порт 8080) необходимо настроить два подключения в меню Admin -> Connections:
    1. bank_postgres (PostgreSQL):
        ◦ Host: bank_postgres
        ◦ Login: admin
        ◦ Password: ваша_база
        ◦ Port: 5432
    2. aws_default (Amazon Web Services):
        ◦ Login: Ваш_Access_Key
        ◦ Password: Ваш_Secret_Key
        ◦ Extra: {"region_name": "ca-central-1"}

## Описание DAG
ID: bank_load_customers_v1 Расписание: @hourly (каждый час)
Этапы работы:
    1. download_and_merge_step: Сканирует папку incoming/ в S3 бакете, скачивает все новые CSV файлы, объединяет их в один DataFrame и сохраняет локально.
    2. upload_to_db_step: Читает объединенный файл, выполняет очистку типов данных и делает UPSERT (добавление новых или обновление существующих) записей в таблицу customers по ключу CustomerId.
    3. Периодичность обновления 1 час.

# 13👥 Участник 3: Analytics & Visualization

## 📊 Ответственность

Настройка Apache Superset, создание визуализаций и интерактивного дашборда для анализа данных о клиентах банка.

---

## ✅ Выполненные задачи

### 🔌 Подключение к базе данных

- Настроил подключение Superset к PostgreSQL (`bank_analytics`)
- Решил проблемы с драйвером psycopg2 и аутентификацией
- Протестировал соединение и обеспечил стабильную работу

### 📁 Создание Dataset

- Импортировал таблицу customers в Superset
- Настроил метаданные: типы данных, описания колонок, форматы
- Подготовил данные для визуализации

### 📈 Разработка визуализаций

| График | Тип | Описание |
|--------|-----|----------|
| Gender Distribution | Pie Chart | Распределение клиентов по полу |
| Age Distribution | Histogram | Распределение по возрастным группам |
| Customers by Geography | Bar Chart | Топ стран/регионов по количеству клиентов |
| Churn Rate | Pie Chart | Доля клиентов, покинувших банк (`Exited`) |
| Active Members | Pie Chart | Активность клиентов (`IsActiveMember`) |

### 🎛 Создание Dashboard

- Разработал интерактивный дашборд `Bank Customers Overview`
- Организовал удобное расположение графиков для быстрого анализа
- Настроил фильтрацию и взаимодействие между элементами

### 📝 Документация

- Описал процесс настройки Superset и подключения к БД
- Задокументировал шаги создания графиков и дашборда
- Подготовил инструкции для команды по работе с визуализациями

---
    
