# IoT Device Status API

A FastAPI-based REST API with SQLite database for managing IoT device status updates.

## Tech Stack

- FastAPI
- SQLModel
- SQLite
- pytest
- Uvicorn

## Project Structure

```
IoT-device-status/
├── app/
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # SQLModel schema definitions
│   └── database.py      # Database configuration and session management
├── tests/
│   ├── test_api.py      # Integration tests (API endpoints)
│   └── unit_tests.py    # Unit tests (model validation)
├── requirements.txt
└── README.md
```

## Design Decisions

1. **SQLModel**: Combines SQLAlchemy + Pydantic for clean, type-safe models
2. **SQLite**: Leverages in-memory database for testing
3. **Latest Status Logic**: Uses `ORDER BY timestamp DESC` for most recent status retrieval
4. **pytest**: testing framework with better fixtures and assertions
5. **FastAPI**: Automatic API documentation, validation, and async support

## API Endpoints

All endpoints require API key authentication via the `x-api-key` header.

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
  -H "x-api-key: api-key-here" \
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
curl -X GET "http://127.0.0.1:8000/status/sensor-abc-123" \
  -H "x-api-key: api-key-here"
```

### Getting Summary

```bash
curl -X GET "http://127.0.0.1:8000/status/summary/" \
  -H "x-api-key: api-key-here"
```

## Testing

### Running Tests

```bash
in the root IoT-device-status directory:

# Run all tests
pytest tests/*

# Run only unit tests
pytest tests/unit_tests.py

# Run only integration tests
pytest tests/test_api.py
```

### Test Coverage

- **Unit Tests**: Model validation, field validation, edge cases
- **Integration Tests**: API endpoints, database operations, error handling

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
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/*
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

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
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
    command: pytest tests/test_api.py
    environment:
      - TEST_DATABASE_URL=sqlite://
```

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://127.0.0.1:8000/docs`

### Environment Variables

Create a `.env` file for local development:

```env
DATABASE_URL=sqlite:///./status.db
API_KEY=api-key-here
```