# API Gateway Security Configuration

Hands-on lab demonstrating API gateway hardening with Kong (local) and
AWS API Gateway (cloud) using Terraform.

## What this project covers

- JWT authentication at the gateway layer
- Rate limiting and throttling
- CORS policy
- Request size validation
- Least-privilege IAM for Lambda
- Infrastructure as Code with Terraform

## Architecture

    Client
      |
      v
    +----------------+     +------------------+
    | Kong Gateway   |---->| Flask Backend    |
    | (localhost)    |     | (localhost:5000) |
    +----------------+     +------------------+

## Local (Kong) setup

### 1. Start the backend

    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python app.py

Backend at http://localhost:5000

### 2. Start Kong

    cd kong
    docker compose up -d

Kong proxy at http://localhost:8000
Kong admin at http://localhost:8001

### 3. Register the service and route

    curl -X POST http://localhost:8001/services --data "name=backend-api" --data "url=http://host.docker.internal:5000"

    curl -X POST http://localhost:8001/services/backend-api/routes --data "name=backend-route" --data "paths[]=/api" --data "strip_path=true"

### 4. Add rate limiting plugin

    curl -X POST http://localhost:8001/services/backend-api/plugins --data "name=rate-limiting" --data "config.minute=20" --data "config.policy=local"

### 5. Add CORS plugin

    curl -X POST http://localhost:8001/services/backend-api/plugins --data "name=cors" --data "config.origins=*" --data "config.methods=GET" --data "config.methods=POST" --data "config.methods=OPTIONS"

### 6. Add request size limiting

    curl -X POST http://localhost:8001/services/backend-api/plugins --data "name=request-size-limiting" --data "config.allowed_payload_size=1"

## Testing

    # Direct to backend
    curl http://localhost:5000/health

    # Through Kong
    curl http://localhost:8000/api/health

    # Login
    curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"alice\",\"password\":\"alice123\"}"

    # Rate limit test (run 25 times)
    1..25 | ForEach-Object { curl -s -o $null -w "%{http_code}`n" http://localhost:8000/api/health }

## Security controls

| Control | Kong | AWS API Gateway |
|---|---|---|
| JWT auth | jwt plugin | JWT authorizer |
| Rate limiting | 20/min | 10 rps, 20 burst |
| CORS | configured | configured |
| Request size | 1 MB | default |
| IAM least privilege | n/a | Lambda exec role |

## Warning
For training only. Do not expose publicly without hardening.
