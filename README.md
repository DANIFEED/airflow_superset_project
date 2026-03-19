# airflow_superset_project

## Current status
- Ubuntu server created
- Docker and Docker Compose installed
- PostgreSQL 15 deployed in Docker
- Database bank_analytics created
- Historical client dataset loaded into table customers
- Total rows loaded: 10000

## PostgreSQL connection
- Host: 52.60.84.64
- Port: 5432
- Database: bank_analytics
- User: bank_admin

## Main table
- customers

## Columns
- Date
- CustomerId
- Surname
- CreditScore
- Geography
- Gender
- Age
- Tenure
- Balance
- NumOfProducts
- HasCrCard
- IsActiveMember
- EstimatedSalary
- Exited

## Run PostgreSQL
docker compose up -d

## Notes
- .env is not committed
- CSV files are not committed
- New clients should be loaded later by Airflow
