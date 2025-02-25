#!/bin/bash

APP_NAME="reproai"
IMAGE_NAME="reproai:dev"
CONTAINER_NAME="reproai"

echo "🛑 Stopping and removing existing container (if any)..."
docker stop $CONTAINER_NAME 2>/dev/null && docker rm $CONTAINER_NAME 2>/dev/null

echo "🗑 Removing old image (if any)..."
docker rmi $IMAGE_NAME 2>/dev/null

echo "🔄 Building new Docker image..."
docker build -t $IMAGE_NAME --build-arg ENV=dev .

echo "🚀 Running new container..."
docker run -d -p 7860:80 --name $CONTAINER_NAME $IMAGE_NAME
