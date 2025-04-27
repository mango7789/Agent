#!/bin/bash
curl -X 'POST' \
  'http://127.0.0.1:8000/scraper' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "param1": "value1",
  "param2": "value2"
}'
