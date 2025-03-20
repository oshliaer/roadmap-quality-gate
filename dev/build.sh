#!/bin/bash

set -a
source .env.local
set +a

set -e

# Configuration
CONTAINER_NAME="roadmap-quality-gate"
IMAGE_NAME="roadmap-quality-gate:latest"
DOCKERFILE_PATH="./Dockerfile"
BUILD_CONTEXT="."

# Colored messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Recreating container ${CONTAINER_NAME}${NC}"

# Check if container is running
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo -e "${YELLOW}Stopping container ${CONTAINER_NAME}...${NC}"
    docker stop ${CONTAINER_NAME}
fi

# Check if container exists
if [ "$(docker ps -a -q -f name=${CONTAINER_NAME})" ]; then
    echo -e "${YELLOW}Removing container ${CONTAINER_NAME}...${NC}"
    docker rm ${CONTAINER_NAME}
fi

# Check if image exists
if [[ "$(docker images -q ${IMAGE_NAME} 2> /dev/null)" != "" ]]; then
    echo -e "${YELLOW}Removing image ${IMAGE_NAME}...${NC}"
    docker rmi ${IMAGE_NAME}
fi

# Build new image
echo -e "${YELLOW}Building new image ${IMAGE_NAME}...${NC}"
docker build -t ${IMAGE_NAME} -f ${DOCKERFILE_PATH} ${BUILD_CONTEXT}

# Run new container
echo -e "${YELLOW}Starting new container ${CONTAINER_NAME}...${NC}"

docker run -d --name ${CONTAINER_NAME} \
    -v "$(pwd)/test:/github" \
    -e WORKSPACE_PATH="/github/workspace" \
    -e GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
    -e GITHUB_TOKEN="${GITHUB_TOKEN}" \
    ${IMAGE_NAME}

echo -e "${GREEN}Container ${CONTAINER_NAME} successfully recreated!${NC}"
echo -e "${GREEN}To view logs run: docker logs -f ${CONTAINER_NAME}${NC}"

# Display initial logs
docker logs -f ${CONTAINER_NAME}
