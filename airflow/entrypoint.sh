#!/bin/bash
set -e

airflow db migrate

airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --skip-if-exists

airflow scheduler &
airflow webserver