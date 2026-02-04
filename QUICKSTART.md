# Quick Start Installation Guide

## 🚀 5-Minute Setup

### Step 1: Prepare Your Raspberry Pi

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install python3 python3-pip -y

# Add user to GPIO group
sudo usermod -a -G gpio $USER
```

### Step 2: Download the Project

```bash
# Create directory
cd ~
mkdir gpio-controller
cd gpio-controller

# Create subdirectories
mkdir backend frontend
```

**Copy these files to your Raspberry Pi:**
- `backend/main.py` → `/home/pi/gpio-controller/backend/`
- `backend/requirements.txt` → `/home/pi/gpio-controller/backend/`
- `frontend/index.html` → `/home/pi/gpio-controller/frontend/`
- `start.sh` → `/home/pi/gpio-controller/`

You can use SCP, FileZilla, or a USB drive.

### Step 3: Install Dependencies

```bash
cd ~/gpio-controller/backend
pip3 install -r requirements.txt
```

### Step 4: Configure the Application

Edit the backend configuration:

```bash
nano ~/gpio-controller/backend/main.py
```

**REQUIRED**: Change the SECRET_KEY (around line 35):

```python
SECRET_KEY = "your-random-secret-key-here"
```

Generate a secure key with:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**REQUIRED**: Update GPIO pins if needed (around line 40):

```python
# GPIO pins with device names (BCM numbering)
GPIO_PINS = {
    35: "Intel NuC PC",
    37: "SDR RF FrontEnd", 
    33: "G5500 Rotator",
    31: "VHF SSPA",
    36: "UHF SSPA",
    38: "Cooling FAN",
    40: "Light",
    29: "Spare"
}
```

Save and exit (Ctrl+X, Y, Enter)

Edit the frontend configuration:

```bash
nano ~/gpio-controller/frontend/index.html
```

Find and update (around line 674):

```javascript
// Replace 'localhost' with your Pi's IP address
apiUrl: 'http://192.168.1.100:8000',  // Change this!
wsUrl: 'ws://192.168.1.100:8000/ws',   // Change this!
```

To find your Pi's IP:
```bash
hostname -I
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Start the Application

```bash
cd ~/gpio-controller
chmod +x start.sh
./start.sh
```

You should see:
```
🎉 GPIO Controller is running!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Web Interface: http://192.168.1.100:3000
🔧 API Docs:      http://192.168.1.100:8000/docs
```

### Step 6: Access the Interface

Open a web browser on any device in your network:

```
http://YOUR_PI_IP:3000
```

**Default login:**
- Username: `admin`
- Password: `admin123`

**⚠️ CHANGE THIS PASSWORD IMMEDIATELY!**

## 🎯 You're Done!

You can now:
- ✅ Control GPIO pins from any device
- ✅ Create multiple user accounts
- ✅ View real-time activity logs
- ✅ Monitor all connected users

---

## 🔧 Optional: Auto-Start on Boot

To make the service start automatically when your Pi boots:

### Option 1: Using Systemd (Recommended)

```bash
# Copy service files
sudo cp ~/gpio-controller/gpio-controller-backend.service /etc/systemd/system/
sudo cp ~/gpio-controller/gpio-controller-frontend.service /etc/systemd/system/

# Edit the service files to match your setup
sudo nano /etc/systemd/system/gpio-controller-backend.service
# Change paths if your project is not in /home/pi/gpio-controller/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable gpio-controller-backend.service
sudo systemctl enable gpio-controller-frontend.service

# Start services
sudo systemctl start gpio-controller-backend.service
sudo systemctl start gpio-controller-frontend.service

# Check status
sudo systemctl status gpio-controller-backend.service
sudo systemctl status gpio-controller-frontend.service
```

### Option 2: Using crontab

```bash
# Edit crontab
crontab -e

# Add this line at the end:
@reboot sleep 30 && cd /home/pi/gpio-controller && ./start.sh
```

---

## 📱 Mobile Access Setup

To access from your phone or tablet:

1. Make sure your device is on the same Wi-Fi network
2. Open browser and go to: `http://YOUR_PI_IP:3000`
3. Add to home screen for quick access:
   - **iOS**: Tap share icon → Add to Home Screen
   - **Android**: Tap menu → Add to Home Screen

---

## 🌐 Internet Access (Advanced)

To access from outside your network:

### Using Tailscale (Easiest & Most Secure)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

# Get your Tailscale IP
tailscale ip -4
```

Access from anywhere using your Tailscale IP!

### Using Port Forwarding (Less Secure)

1. Log into your router
2. Forward ports 8000 and 3000 to your Pi's IP
3. Get your public IP: `curl ifconfig.me`
4. Access using: `http://YOUR_PUBLIC_IP:3000`

⚠️ **Security Warning**: Use HTTPS and strong passwords!

---

## 🛠️ Common Commands

```bash
# View backend logs
journalctl -u gpio-controller-backend.service -f

# View frontend logs
journalctl -u gpio-controller-frontend.service -f

# Restart backend
sudo systemctl restart gpio-controller-backend.service

# Stop everything
sudo systemctl stop gpio-controller-backend.service
sudo systemctl stop gpio-controller-frontend.service

# Check API directly
curl http://localhost:8000/

# Check if ports are open
netstat -tlnp | grep -E "8000|3000"
```

---

## ❓ Troubleshooting

### "Permission denied" error
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

### Can't access from other devices
```bash
# Check firewall
sudo ufw status

# Allow ports if firewall is active
sudo ufw allow 8000
sudo ufw allow 3000
```

### Backend won't start
```bash
# Check if port is in use
sudo netstat -tlnp | grep 8000

# Check Python version (needs 3.8+)
python3 --version

# Reinstall dependencies
cd ~/gpio-controller/backend
pip3 install -r requirements.txt --upgrade
```

### WebSocket not connecting
- Verify the `wsUrl` in `frontend/index.html` matches your Pi's IP
- Check browser console for errors (F12)
- Ensure backend is running

### GPIO not working
```bash
# Test GPIO manually
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, GPIO.HIGH); print('Pin 17 should be HIGH now')"

# Check GPIO permissions
ls -l /dev/gpiomem
```

---

## 📚 Next Steps

- Read `README.md` for detailed documentation
- Check `CONFIGURATION.md` for advanced settings
- Explore the API docs at `http://YOUR_PI_IP:8000/docs`
- Create additional user accounts
- Set up scheduled GPIO tasks
- Add email notifications

---

## 🆘 Need Help?

1. Check the logs: `journalctl -u gpio-controller-backend.service -f`
2. Verify network connectivity: `ping 192.168.1.100`
3. Test API directly: `curl http://localhost:8000/`
4. Check browser console (F12)

---

## 🎉 Enjoy your GPIO Controller!

Remember to:
- ⚠️ Change the default admin password
- 🔒 Use strong passwords for all accounts
- 🌐 Secure your network
- 📝 Keep logs for security monitoring
