#!/bin/bash
JOB_ID="6827ed530cb2e84f544d14f6"

curl -X POST \
  "http://127.0.0.1:8000/matcher/${JOB_ID}" \
  -H "accept: application/json"