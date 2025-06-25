# IoT Device Status API

A FastAPI-based REST API for managing IoT device status updates.

## API Endpoints

- `POST /status/` - Create a new device status
- `GET /status/` - Get all device statuses
- `GET /status/{device_id}` - Get latest status for a specific device
- `GET /status/summary/` - Get summary of all devices
- `PATCH /status/{device_id}` - Update device status
- `DELETE /status/{device_id}` - Delete device status

## Setup

### Prerequisites

- Python 3.9+

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd IoT-device-status
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

The server will start on `http://127.0.0.1:8000`

## Usage

### Creating a Device Status

```bash
curl -X POST "http://127.0.0.1:8000/status/" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "sensor-abc-123",
    "timestamp": "2025-06-09T14:00:00Z",
    "battery_level": 76,
    "rssi": -60,
    "online": true
  }'
```

### Getting Latest Status

```bash
curl -X GET "http://127.0.0.1:8000/status/sensor-abc-123"
```

### Getting Summary

```bash
curl -X GET "http://127.0.0.1:8000/status/summary/"
```

## Testing

### Running Tests

```bash
# Run integration tests
python tests/test_api.py

# Run unit tests
python tests/unit_tests.py

# Run all tests
python -m unittest discover tests/ -v

```

### Test Coverage

The test suite includes:
- **Unit Tests**: Model validation and making sure devices are stored correctly in the database
- **Integration Tests**: API endpoint testing with in-memory database

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/ci.yml`:

```yaml
  name: Test
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v2
        - name: Set up Python
          uses: actions/setup-python@v2
          with:
            python-version: 3.9
        - name: Install dependencies
          run: pip install fastapi uvicorn sqlmodel httpx
        - name: Run tests
          run: python -m unittest discover tests/ -v
```

### Docker Integration

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["python", "app/main.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./status.db
    volumes:
      - ./data:/app/data

  test:
    build: .
    command: python tests/test_api.py
    environment:
      - TEST_DATABASE_URL=sqlite:///:memory:
```

## Development

### Project Structure

```
IoT-device-status/
├── app/
│   ├── main.py          # FastAPI application
│   ├── models.py        # SQLModel definitions
│   └── database.py      # Database configuration
├── tests/
│   ├── test_api.py      # Integration tests
│   └── unit_tests.py    # Unit tests
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md          # This file
```

### Design Decisions

1. SQLModel: combines SQLAlchemy + Pydantic for clean models
2. SQLite to leverage its in-memory database for testing
3. Latest Status: uses ```ORDER BY timestamp DESC``` for most recent status update
4. Simple Structure: flat organization given project scope
