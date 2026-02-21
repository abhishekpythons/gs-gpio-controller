import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flask_socketio import SocketIO

from gpio import get_pins_state, set_pin
from auth import create_user, verify_user
from db import init_db, log_action, get_logs

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "change-this-secret"

CORS(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")

init_db()

@app.post("/api/register")
def register():
    data = request.json
    create_user(data["username"], data["password"])
    token = create_access_token(identity=data["username"])
    log_action(data["username"], "REGISTER")
    return jsonify(access_token=token)

@app.post("/api/login")
def login():
    data = request.json
    if not verify_user(data["username"], data["password"]):
        return jsonify(detail="Invalid credentials"), 401
    token = create_access_token(identity=data["username"])
    log_action(data["username"], "LOGIN")
    return jsonify(access_token=token)

@app.get("/api/user/me")
@jwt_required()
def me():
    return jsonify(username=get_jwt_identity())

@app.get("/api/gpio/pins")
@jwt_required()
def gpio_pins():
    return jsonify(pins=get_pins_state())

@app.post("/api/gpio/control")
@jwt_required()
def gpio_control():
    data = request.json
    user = get_jwt_identity()

    ok = set_pin(data["pin"], data["state"])
    if not ok:
        return jsonify(error="Invalid pin"), 400

    log_action(
        user,
        "GPIO_CONTROL",
        data["pin"],
        "HIGH" if data["state"] else "LOW"
    )

    socketio.emit("message", {
        "type": "gpio_update",
        "pin": data["pin"],
        "state": data["state"],
        "user": user
    })

    return jsonify(success=True)

@app.get("/api/logs")
@jwt_required()
def logs():
    limit = int(request.args.get("limit", 50))
    return jsonify(logs=get_logs(limit))

@socketio.on("connect")
def ws_connect():
    print("WebSocket connected")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
