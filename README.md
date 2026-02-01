# Raspberry Pi GPIO Web Controller

A modern, real-time web-based GPIO controller for Raspberry Pi with user authentication, activity logging, and WebSocket-powered live updates.

## Features

- 🔐 **Secure Authentication**: JWT-based login system with encrypted passwords
- ⚡ **Real-time Updates**: WebSocket integration for instant GPIO state synchronization
- 📊 **Activity Logging**: Complete audit trail of all GPIO operations and user access
- 🎨 **Modern UI**: Beautiful, responsive Vue.js interface with gradient aesthetics
- 🔌 **GPIO Control**: Control up to 8 GPIO pins remotely from anywhere on your network
- 📱 **Mobile Friendly**: Responsive design works on all devices
- 🗄️ **Database Tracking**: SQLite database for persistent user and log storage

## Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework with async support
- **SQLite**: Lightweight database for users and logs
- **JWT**: Secure token-based authentication
- **WebSocket**: Real-time bidirectional communication
- **bcrypt**: Secure password hashing

### Frontend
- **Vue.js 3**: Progressive JavaScript framework
- **WebSocket API**: Real-time updates without page refresh
- **Custom CSS**: Modern gradient design with animations
- **Responsive Layout**: Works on desktop, tablet, and mobile

## Installation

### Prerequisites

- Raspberry Pi (3/4/5 or Zero W) with Raspbian/Raspberry Pi OS
- Python 3.8 or higher
- Network connection

### Step 1: Clone or Download Files

```bash
# Create project directory
mkdir gpio-controller
cd gpio-controller

# Create backend and frontend directories
mkdir backend frontend
```

Place the following files in their respective directories:
- `backend/main.py` - FastAPI server
- `backend/requirements.txt` - Python dependencies
- `frontend/index.html` - Vue.js web interface

### Step 2: Install Python Dependencies

```bash
cd backend

# Install pip if not already installed
sudo apt-get update
sudo apt-get install python3-pip

# Install required packages
pip3 install -r requirements.txt
```

### Step 3: Enable GPIO (On Raspberry Pi)

```bash
# Add your user to the gpio group
sudo usermod -a -G gpio $USER

# Reboot to apply changes
sudo reboot
```

### Step 4: Configure the Application

Edit `backend/main.py` and update:

```python
# IMPORTANT: Change this in production!
SECRET_KEY = "your-secret-key-change-this-in-production"

# GPIO pins you want to control (BCM numbering)
GPIO_PINS = [17, 18, 27, 22, 23, 24, 25, 4]
```

Edit `frontend/index.html` and update the API URL:

```javascript
// Change localhost to your Raspberry Pi's IP address
apiUrl: 'http://192.168.1.100:8000',
wsUrl: 'ws://192.168.1.100:8000/ws',
```

## Running the Application

### Start the Backend Server

```bash
cd backend
python3 main.py
```

The server will start on `http://0.0.0.0:8000`

### Serve the Frontend

Option 1: Using Python's built-in HTTP server:

```bash
cd frontend
python3 -m http.server 3000
```

Access at: `http://192.168.1.100:3000` (replace with your Pi's IP)

Option 2: Using a web server like nginx or Apache (recommended for production)

## Default Login

When you first run the application, a default admin account is created:

- **Username**: `admin`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change this password immediately after first login by creating a new user!

## Usage

### Web Interface

1. **Login/Register**
   - Open the web interface in your browser
   - Login with default credentials or register a new account
   - Your session will be saved for 24 hours

2. **Control GPIO Pins**
   - Click any GPIO pin card to toggle it ON/OFF
   - Pin state changes are instant and visible to all connected users
   - Current state is shown with a colored indicator

3. **Monitor Activity**
   - View real-time activity log in the right panel
   - See who accessed the system and when
   - Track all GPIO state changes with timestamps

4. **Real-time Updates**
   - Connection status shown in header ("LIVE" when connected)
   - All users see GPIO changes instantly via WebSocket
   - Automatic reconnection if connection is lost

## API Endpoints

### Authentication

- `POST /api/register` - Register new user
  ```json
  {
    "username": "john",
    "password": "secure123",
    "email": "john@example.com"
  }
  ```

- `POST /api/login` - Login user
  ```json
  {
    "username": "john",
    "password": "secure123"
  }
  ```

- `GET /api/user/me` - Get current user info (requires auth)

### GPIO Control

- `GET /api/gpio/pins` - Get all GPIO pins and states (requires auth)

- `POST /api/gpio/control` - Control GPIO pin (requires auth)
  ```json
  {
    "pin": 17,
    "state": 1
  }
  ```

### Activity Logs

- `GET /api/logs?limit=50` - Get activity logs (requires auth)

### WebSocket

- `WS /ws` - WebSocket endpoint for real-time updates

## Database Schema

### Users Table
```sql
- id: INTEGER PRIMARY KEY
- username: TEXT UNIQUE
- password_hash: TEXT
- email: TEXT
- created_at: TIMESTAMP
- is_active: BOOLEAN
```

### Access Logs Table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER
- username: TEXT
- action: TEXT (LOGIN, REGISTER, GPIO_CONTROL)
- pin: INTEGER
- state: TEXT (HIGH, LOW)
- timestamp: TIMESTAMP
```

### GPIO State Table
```sql
- pin: INTEGER PRIMARY KEY
- state: INTEGER (0 or 1)
- last_updated: TIMESTAMP
```

## GPIO Pin Mapping (BCM Mode)

The application uses BCM (Broadcom) pin numbering:

```
Default Pins: 17, 18, 27, 22, 23, 24, 25, 4

Physical Pin Layout (for reference):
3V3  (1) (2)  5V
GP2  (3) (4)  5V
GP3  (5) (6)  GND
GP4  (7) (8)  GP14
GND  (9) (10) GP15
GP17 (11) (12) GP18
GP27 (13) (14) GND
GP22 (15) (16) GP23
3V3  (17) (18) GP24
GP10 (19) (20) GND
GP9  (21) (22) GP25
GP11 (23) (24) GP8
GND  (25) (26) GP7
```

## Security Considerations

1. **Change Default Credentials**: The default admin account should be removed or password changed
2. **Use HTTPS**: In production, use HTTPS for encrypted communication
3. **Firewall Rules**: Configure firewall to restrict access to trusted networks
4. **Strong Passwords**: Enforce strong password policies
5. **Secret Key**: Change the JWT SECRET_KEY to a random, secure value
6. **Network Isolation**: Consider running on an isolated network segment

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is already in use
sudo netstat -tlnp | grep 8000

# Try a different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

### GPIO Permission Denied
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER
sudo reboot
```

### WebSocket Connection Failed
- Ensure backend is running
- Check firewall settings
- Verify correct IP address in frontend configuration
- Check browser console for error messages

### Can't Access from Other Devices
```bash
# Check Raspberry Pi's IP address
hostname -I

# Ensure firewall allows connections
sudo ufw allow 8000
sudo ufw allow 3000
```

## Development & Testing

### Testing Without Raspberry Pi

The application includes a mock GPIO module for development and testing on non-Raspberry Pi systems:

```bash
# Run on any computer with Python
cd backend
python3 main.py
```

The mock GPIO will simulate pin states without requiring actual hardware.

### API Testing with cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}' | jq -r '.access_token')

# Get GPIO pins
curl http://localhost:8000/api/gpio/pins \
  -H "Authorization: Bearer $TOKEN"

# Toggle GPIO pin
curl -X POST http://localhost:8000/api/gpio/control \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"pin":17,"state":1}'
```

## Running as a System Service

To run the application automatically on boot:

```bash
# Create systemd service file
sudo nano /etc/systemd/system/gpio-controller.service
```

Add the following:

```ini
[Unit]
Description=GPIO Controller API
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/gpio-controller/backend
ExecStart=/usr/bin/python3 /home/pi/gpio-controller/backend/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable gpio-controller
sudo systemctl start gpio-controller
sudo systemctl status gpio-controller
```

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review the API documentation
3. Check browser console for errors
4. Verify network connectivity and firewall settings
