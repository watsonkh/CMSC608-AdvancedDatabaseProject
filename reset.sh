#!/bin/sh

python tx.py

source flask/.env
if [ -z "$PORT" ]; then
  PORT= 5432
fi
if [ -z "$HOST" ]; then
  HOST=localhost
fi
psql -h ${HOST} -p ${PORT} -U ${USER} ${DATABASE} -f data/drop.sql
psql -h ${HOST} -p ${PORT} -U ${USER} ${DATABASE} -f data/tables.sql
psql -h ${HOST} -p ${PORT} -U ${USER} ${DATABASE} -f data/data.sql
psql -h ${HOST} -p ${PORT} -U ${USER} ${DATABASE} -f output.sql

cd flask
python embeddings.py
cd -

