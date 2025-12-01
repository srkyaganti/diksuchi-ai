#!/bin/bash

# Health Check Script - Verify All Services (macOS)

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Diksuchi-AI Platform Health Check"
echo "=========================================="

# Function to check service
check_service() {
    local name=$1
    local url=$2

    if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q "200"; then
        echo "✓ $name: HEALTHY"
        return 0
    else
        echo "✗ $name: UNHEALTHY"
        return 1
    fi
}

# Check PostgreSQL
echo -n "PostgreSQL:  "
if psql -U postgres -h localhost -p 5432 -d diksuchi -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✓ HEALTHY"
else
    echo "✗ UNHEALTHY"
fi

# Check Redis
echo -n "Redis:       "
if redis-cli -h localhost -p 6379 ping 2>/dev/null | grep -q "PONG"; then
    echo "✓ HEALTHY"
else
    echo "✗ UNHEALTHY"
fi

# Check ChromaDB
check_service "ChromaDB    " "http://localhost:8000/api/v1/heartbeat"

# Check RAG Service
check_service "RAG Service " "http://localhost:5001/health"

# Check TTS Service
check_service "TTS Service " "http://localhost:8002/health"

# Check Web App
check_service "Web App     " "http://localhost:3000"

echo "=========================================="
echo "Health check complete!"
echo ""
echo "To view logs:"
echo "  tail -f logs/chromadb.log"
echo "  tail -f logs/rag-service.log"
echo "  tail -f logs/tts-service.log"
echo "  tail -f logs/web-app.log"
echo ""
echo "External Services (manage separately):"
echo "  LM Studio:   localhost:1234 (LLM inference)"
echo "  whisper.cpp: localhost:8080 (Speech-to-Text)"
echo "=========================================="
