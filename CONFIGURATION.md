# GPIO Controller Configuration Guide

## Backend Configuration (backend/main.py)

### Security Settings

```python
# CRITICAL: Change this to a random secret key in production
# Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY = "your-secret-key-change-this-in-production"

# JWT token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
```

### GPIO Pin Configuration

```python
# Define which GPIO pins to control (BCM numbering)
# You can add or remove pins based on your needs
GPIO_PINS = [17, 18, 27, 22, 23, 24, 25, 4]

# Common GPIO pins you might want to use:
# GPIO 2, 3, 4, 17, 27, 22, 10, 9, 11, 5, 6, 13, 19, 26
# GPIO 14, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 21
```

### Database Configuration

```python
# SQLite database file path
DB_PATH = "gpio_controller.db"

# To use a different location:
# DB_PATH = "/var/lib/gpio-controller/database.db"
```

### Default Admin Account

```python
# Change the default admin credentials in init_db() function
admin_hash = bcrypt.hashpw("YOUR_SECURE_PASSWORD".encode('utf-8'), bcrypt.gensalt())
cursor.execute('''
    INSERT OR IGNORE INTO users (username, password_hash, email) 
    VALUES (?, ?, ?)
''', ("admin", admin_hash.decode('utf-8'), "your-email@example.com"))
```

### Server Settings

```python
# At the bottom of main.py, change host and port if needed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,       # Change port if needed
        # For production, add:
        # ssl_keyfile="path/to/key.pem",
        # ssl_certfile="path/to/cert.pem"
    )
```

## Frontend Configuration (frontend/index.html)

### API Connection Settings

```javascript
data() {
    return {
        // Change these to match your Raspberry Pi's IP address
        apiUrl: 'http://192.168.1.100:8000',
        wsUrl: 'ws://192.168.1.100:8000/ws',
        
        // For HTTPS (production):
        // apiUrl: 'https://192.168.1.100:8000',
        // wsUrl: 'wss://192.168.1.100:8000/ws',
        
        // For domain name:
        // apiUrl: 'https://gpio.yourdomain.com',
        // wsUrl: 'wss://gpio.yourdomain.com/ws',
    }
}
```

### Theme Customization

Find the `:root` CSS variables in the `<style>` section:

```css
:root {
    /* Change these colors to customize the theme */
    --bg-primary: #0a0e27;        /* Main background */
    --bg-secondary: #111633;      /* Card backgrounds */
    --bg-card: #1a1f3a;           /* Inner card elements */
    --accent-primary: #00ff88;    /* Primary accent (green) */
    --accent-secondary: #0099ff;  /* Secondary accent (blue) */
    --accent-danger: #ff0055;     /* Danger/error color */
    --text-primary: #ffffff;      /* Primary text */
    --text-secondary: #8899aa;    /* Secondary text */
    --text-muted: #556677;        /* Muted text */
    --border-color: #2a3050;      /* Border color */
}
```

## Environment-Specific Configurations

### Development (Your Computer)

```python
# backend/main.py
DEBUG = True
TESTING = True

# Use mock GPIO
GPIO_AVAILABLE = False
```

### Production (Raspberry Pi)

```python
# backend/main.py
DEBUG = False
TESTING = False

# Use real GPIO
# The code automatically detects if RPi.GPIO is available
```

## Network Configuration

### Local Network Only (Default)

No additional configuration needed. Access via:
- http://192.168.1.100:8000 (backend)
- http://192.168.1.100:3000 (frontend)

### Internet Access (Advanced)

1. **Port Forwarding**: Configure your router to forward ports 8000 and 3000
2. **Dynamic DNS**: Use a service like No-IP or DuckDNS
3. **HTTPS**: Use Let's Encrypt for SSL certificates
4. **Reverse Proxy**: Use nginx to serve both frontend and backend

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name gpio.yourdomain.com;

    # Frontend
    location / {
        root /home/pi/gpio-controller/frontend;
        index index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

## Security Hardening

### 1. Generate Secure Secret Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use the output as your SECRET_KEY

### 2. Enable Firewall

```bash
sudo ufw enable
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 8000/tcp   # Backend
sudo ufw allow 3000/tcp   # Frontend
```

### 3. Restrict Network Access

Edit backend/main.py CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.1.100:3000",  # Specific frontend
        "https://yourdomain.com"       # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Use HTTPS

Install certbot and get SSL certificates:

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d yourdomain.com
```

Update uvicorn.run() in main.py:

```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    ssl_keyfile="/etc/letsencrypt/live/yourdomain.com/privkey.pem",
    ssl_certfile="/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
)
```

## GPIO Hardware Configuration

### Example: Controlling Relays

```python
# Wire relays to GPIO pins
RELAY_PINS = {
    'light': 17,    # Living room light
    'fan': 18,      # Ceiling fan
    'heater': 27,   # Space heater
    'pump': 22      # Water pump
}

# Set all as outputs
for pin in RELAY_PINS.values():
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
```

### Example: Reading Sensors

To add input pins (not included by default):

```python
# Add to main.py
SENSOR_PINS = [5, 6, 13]

for pin in SENSOR_PINS:
    gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

# Create endpoint to read sensors
@app.get("/api/gpio/read/{pin}")
async def read_gpio(pin: int, current_user: dict = Depends(verify_token)):
    if pin not in SENSOR_PINS:
        raise HTTPException(status_code=400, detail="Invalid sensor pin")
    
    value = gpio.input(pin)
    return {"pin": pin, "value": value}
```

## Advanced Features

### Email Notifications

Add email alerts when GPIO pins change:

```python
import smtplib
from email.message import EmailMessage

def send_email_alert(pin, state, user):
    msg = EmailMessage()
    msg.set_content(f"GPIO Pin {pin} changed to {state} by {user}")
    msg['Subject'] = f'GPIO Alert - Pin {pin}'
    msg['From'] = 'gpio@yourdomain.com'
    msg['To'] = 'admin@yourdomain.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your-email@gmail.com', 'your-app-password')
        server.send_message(msg)

# Call in control_gpio function
send_email_alert(control.pin, control.state, current_user["username"])
```

### Scheduled GPIO Control

Add APScheduler for timed operations:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=6, minute=0)
async def morning_routine():
    # Turn on lights at 6 AM
    gpio.output(17, gpio.HIGH)

scheduler.start()
```

### GPIO State Persistence

The application already saves GPIO states to the database. On restart, restore previous states:

```python
def restore_gpio_states():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT pin, state FROM gpio_state")
    for pin, state in cursor.fetchall():
        gpio.output(pin, gpio.HIGH if state == 1 else gpio.LOW)
    conn.close()

# Call in lifespan startup
restore_gpio_states()
```

## Troubleshooting Configuration

### Check Current Configuration

```bash
# View backend config
grep -E "SECRET_KEY|GPIO_PINS|ACCESS_TOKEN" backend/main.py

# Check which port backend is using
netstat -tlnp | grep python

# View database
sqlite3 gpio_controller.db "SELECT * FROM users;"
```

### Reset Everything

```bash
# Stop services
./stop.sh  # or Ctrl+C

# Remove database
rm backend/gpio_controller.db

# Remove logs
rm *.log

# Restart
./start.sh
```
