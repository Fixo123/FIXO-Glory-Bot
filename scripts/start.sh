#!/bin/bash
# FIXO DEV — Guild Glory Bot Startup Script

echo "🔥 FIXO DEV — Guild Glory Bot"
echo "================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
cd backend
pip install -r requirements.txt

# Start backend
echo -e "${GREEN}🚀 Starting Backend Server...${NC}"
python3 main.py &
BACKEND_PID=$!

# Start frontend
echo -e "${GREEN}🌐 Starting Frontend Server...${NC}"
cd ../frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ FIXO DEV Running!${NC}"
echo -e "📡 Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "🌐 Frontend: ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"

# Wait for interrupt
wait $BACKEND_PID $FRONTEND_PID