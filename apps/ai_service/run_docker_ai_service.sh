#!/bin/bash
IMAGE_NAME="gcp-ai-service:latest"
#   2. Build the Docker image:
docker build -t $IMAGE_NAME  .

#   3. Run the container locally (injecting your credentials just like compose did):
PORT_NUM=${1:-8080}
docker run -d -p $PORT_NUM:$PORT_NUM \
    -e PORT=$PORT_NUM \
    --name ai_service \
    --network ringisho-net \
    --dns 8.8.8.8 \
    -v $(pwd)/../../keys/application_default_credentials.json:/app/keys/application_default_credentials.json:ro \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/keys/application_default_credentials.json \
    $IMAGE_NAME
