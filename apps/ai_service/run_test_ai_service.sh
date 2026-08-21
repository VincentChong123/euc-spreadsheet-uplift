#!/bin/bash
set -e

echo "check firewall status"
cat /etc/ufw/ufw.conf | grep ENABLED

echo "Starting AI Service natively on the host machine for local development..."

cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Default to port 8080 unless specified
PORT_NUM=${1:-8080}
export PORT=$PORT_NUM
export IS_DEV=true

echo "Running AI Service on http://0.0.0.0:$PORT_NUM with auto-reload..."
echo ""
echo "================================================================="
echo "NOTE FOR API-GATEWAY COMMUNICATION:"
echo "Because ai-service is running directly on your Linux host machine"
echo "and NOT inside a Docker container, the api-gateway Docker container"
echo "cannot reach it via 'http://ai_service:8080'."
echo ""
echo "To allow the api-gateway container to communicate with this process,"
echo "you must point its AI_SERVICE_URL to the Docker Host IP (docker0 bridge)."
echo ""
echo "When running api_gateway, pass the host IP as the argument, e.g.:"
echo "  cd ../api_gateway"
echo '  ./run_api_gateway.sh "http://172.17.0.1:'"$PORT_NUM"'"'
echo "================================================================="
echo ""

# Use uvicorn to run the app with live-reloading enabled for code changes
uvicorn main:app --host 0.0.0.0 --port $PORT_NUM --reload
