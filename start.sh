#!/bin/bash

# GPIO Controller Startup Script
# This script starts both backend and frontend servers

echo "🚀 Starting GPIO Controller..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${GREEN}✓ Detected Raspberry Pi${NC}"
else
    echo -e "${BLUE}ℹ Running in development mode (mock GPIO)${NC}"
fi

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python dependencies are installed
echo -e "\n${BLUE}Checking Python dependencies...${NC}"
cd "$SCRIPT_DIR/backend"

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${RED}✗ Dependencies not installed${NC}"
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install dependencies${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Dependencies ready${NC}"

# Get local IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo -e "\n${BLUE}Network Information:${NC}"
echo "  Local IP: $IP_ADDRESS"
echo "  Backend will run on: http://$IP_ADDRESS:8000"
echo "  Frontend will run on: http://$IP_ADDRESS:3000"

# Create a function to cleanup on exit
cleanup() {
    echo -e "\n\n${BLUE}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo -e "\n${BLUE}Starting backend server...${NC}"
cd "$SCRIPT_DIR/backend"
python3 main.py > ../backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend server started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start backend server${NC}"
    echo "Check backend.log for errors"
    exit 1
fi

# Start frontend server
echo -e "\n${BLUE}Starting frontend server...${NC}"
cd "$SCRIPT_DIR/frontend"
python3 -m http.server 3000 > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 1

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend server started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start frontend server${NC}"
    echo "Check frontend.log for errors"
    kill $BACKEND_PID
    exit 1
fi

# Display access information
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 GPIO Controller is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${BLUE}Access the application:${NC}"
echo -e "  🌐 Web Interface: ${GREEN}http://$IP_ADDRESS:3000${NC}"
echo -e "  🔧 API Docs:      ${GREEN}http://$IP_ADDRESS:8000/docs${NC}"
echo -e "\n${BLUE}Default Login:${NC}"
echo -e "  👤 Username: ${GREEN}admin${NC}"
echo -e "  🔑 Password: ${GREEN}admin123${NC}"
echo -e "  ${RED}⚠️  Change this password immediately!${NC}"
echo -e "\n${BLUE}Logs:${NC}"
echo -e "  Backend:  tail -f $SCRIPT_DIR/backend.log"
echo -e "  Frontend: tail -f $SCRIPT_DIR/frontend.log"
echo -e "\n${BLUE}Press Ctrl+C to stop all servers${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Wait for user to stop
wait $BACKEND_PID $FRONTEND_PID
