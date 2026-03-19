import logging
import pandas as pd
import os
import numpy as np
from io import StringIO
from datetime import datetime
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

# Твои данные
BUCKET_NAME = 'airflow-superset-bank-data-2026-342996267294-ca-central-1-an'
S3_PREFIX = 'incoming/'
CONN_ID = 'bank_postgres'
S3_CONN_ID = 'aws_default'
MERGED_FILE_PATH = '/opt/airflow/data/merged_clients.csv'

@dag(
    dag_id='bank_load_customers_v1',
    schedule_interval='@hourly',
    start_date=datetime(2026, 3, 19),
    catchup=False,
    tags=['stars25']
)
def bank_etl():

    @task
    def download_and_merge_step():
        # Явно форсируем регион бакета ca-central-1
        s3_hook = S3Hook(aws_conn_id=S3_CONN_ID)
        
        try:
            keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=S3_PREFIX)
        except Exception as e:
            logging.error(f"S3 Connection Error: {e}")
            raise

        csv_keys = [k for k in keys if k.endswith('.csv')] if keys else []
        
        if not csv_keys:
            logging.info("Файлы не найдены.")
            return None

        all_dfs = []
        for key in csv_keys:
            file_content = s3_hook.read_key(key, BUCKET_NAME)
            df = pd.read_csv(StringIO(file_content), sep=None, engine='python')
            df.columns = df.columns.str.strip()
            all_dfs.append(df)
        
        merged_df = pd.concat(all_dfs, ignore_index=True)
        merged_df.to_csv(MERGED_FILE_PATH, index=False)
        return MERGED_FILE_PATH

    @task
    def upload_to_db_step(file_path: str):
        if not file_path or not os.path.exists(file_path):
            return

        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df = df.replace({np.nan: None})
        
        pg_hook = PostgresHook(postgres_conn_id=CONN_ID)
        
        upsert_sql = """
            INSERT INTO customers (
                "Date", "CustomerId", "Surname", "CreditScore", "Geography", 
                "Gender", "Age", "Tenure", "Balance", "NumOfProducts", 
                "HasCrCard", "IsActiveMember", "EstimatedSalary", "Exited"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ("CustomerId") 
            DO UPDATE SET 
                "Date" = EXCLUDED."Date",
                "Surname" = EXCLUDED."Surname",
                "CreditScore" = EXCLUDED."CreditScore",
                "Geography" = EXCLUDED."Geography",
                "Gender" = EXCLUDED."Gender",
                "Age" = EXCLUDED."Age",
                "Tenure" = EXCLUDED."Tenure",
                "Balance" = EXCLUDED."Balance",
                "NumOfProducts" = EXCLUDED."NumOfProducts",
                "HasCrCard" = EXCLUDED."HasCrCard",
                "IsActiveMember" = EXCLUDED."IsActiveMember",
                "EstimatedSalary" = EXCLUDED."EstimatedSalary",
                "Exited" = EXCLUDED."Exited";
        """

        conn = pg_hook.get_conn()
        cur = conn.cursor()
        try:
            for _, row in df.iterrows():
                cur.execute(upsert_sql, tuple(row))
            conn.commit()
            logging.info(f"Загружено строк: {len(df)}")
        finally:
            cur.close()
            conn.close()
            if os.path.exists(file_path):
                os.remove(file_path)

    upload_to_db_step(download_and_merge_step())

bank_etl_dag = bank_etl()