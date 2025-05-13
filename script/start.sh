#!/bin/bash
docker run --runtime=runc --name resume-mongo -v /home/resume/data/mongodb/backup:/data/db/backup -d -p 27017:27017 mongo 
docker run --runtime=runc --name resume-redis -d -p 6379:6379 redis