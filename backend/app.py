"""
Backend API secured behind Kong / AWS API Gateway.
Issues and verifies short-lived JWTs.
"""

from flask import Flask, request, jsonify
import jwt
import datetime
import os

app = Flask(__name__)
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGO = "HS256"
JWT_AUD = "gateway-lab"
JWT_ISS = "api-gateway-security"


def issue_token(user_id, roles):
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "roles": roles,
            "iat": now,
            "exp": now + datetime.timedelta(minutes=15),
            "iss": JWT_ISS,
            "aud": JWT_AUD,
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )


def verify_token(token):
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGO],
        audience=JWT_AUD,
        issuer=JWT_ISS,
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/auth/login", methods=["POST"])
def login():
    body = request.get_json() or {}
    user = body.get("username")
    pw = body.get("password")
    # Demo only. Replace with DB + bcrypt in production.
    if user == "alice" and pw == "alice123":
        return jsonify({"token": issue_token("alice", ["user"])})
    if user == "admin" and pw == "admin123":
        return jsonify({"token": issue_token("admin", ["admin", "user"])})
    return jsonify({"error": "invalid credentials"}), 401


@app.route("/me", methods=["GET"])
def me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401
    try:
        data = verify_token(auth.split(" ", 1)[1])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid token"}), 401
    return jsonify({"user": data["sub"], "roles": data["roles"]})


@app.route("/admin", methods=["GET"])
def admin():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401
    try:
        data = verify_token(auth.split(" ", 1)[1])
    except jwt.InvalidTokenError:
        return jsonify({"error": "invalid token"}), 401
    if "admin" not in data.get("roles", []):
        return jsonify({"error": "forbidden"}), 403
    return jsonify({"message": "admin access granted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
