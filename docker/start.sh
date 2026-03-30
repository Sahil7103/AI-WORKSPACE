#!/bin/bash

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Initialize database
echo "Initializing database..."
docker-compose -f docker/docker-compose.yml exec -T backend python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
print('Database initialized!')
"

echo "✅ Services started successfully!"
echo ""
echo "Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - Nginx: http://localhost:80"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "API Docs: http://localhost:8000/docs"
