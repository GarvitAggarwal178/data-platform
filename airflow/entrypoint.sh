#!/bin/bash
set -e

airflow db migrate

# check if admin user already exists, only create if it doesn't
airflow users list | grep -q "admin" || airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com

airflow scheduler &
airflow webserver