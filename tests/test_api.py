from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
import unittest

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app
from app.database import get_session
from app.models import DeviceStatus


class TestStatusAPI(unittest.TestCase):
  """Integration Tests for status API"""

  def setUp(self):
    """set up test database and client before each test"""
    TEST_DATABASE_URL = "sqlite:///:memory:"
    self.engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    print("creating tables...\n")
    SQLModel.metadata.create_all(self.engine)

    def get_test_session():
        with Session(self.engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    self.client = TestClient(app)

  def tearDown(self):
    """clean up after every test"""
    app.dependency_overrides.clear()

  """
  /status/ TESTS
  """

  def test_create_and_get_status(self):
    """test POST and GET endpoints"""

    status = {
        "device_id": "sensor-abc-123",
        "timestamp": "2025-06-09T14:00:00Z",
        "battery_level": 76,
        "rssi": -60,
        "online": True,
    }

    # POST /status/
    response = self.client.post("/status/", json=status)
    status = response.json()
    assert response.status_code == 201
    assert status["device_id"] == "sensor-abc-123"
    assert status["battery_level"] == 76
    assert status["rssi"] == -60
    assert status["online"] == True

    # GET /status/sensor-abc-123
    response = self.client.get("/status/sensor-abc-123")
    status = response.json()
    assert response.status_code == 200
    assert status["device_id"] == "sensor-abc-123"
    assert status["battery_level"] == 76
    assert status["rssi"] == -60
    assert status["online"] == True

  def test_get_latest_status_different_dates(self):
    """tests GET returns latest status for a device with multiple updates on different days"""
    device_id = "test-sensor-1"

    statuses = [
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T14:00:00Z",
        "battery_level": 85,
        "rssi": -50,
        "online": True,
      },
      {
        "device_id": device_id,
        "timestamp": "2025-06-30T7:00:00Z",  # latest update (expected return)
        "battery_level": 30,
        "rssi": -20,
        "online": False,
      },
      {
        "device_id": device_id,
        "timestamp": "2025-06-23T11:00:00Z",
        "battery_level": 100,
        "rssi": -30,
        "online": True,
      },
    ]

    for status in statuses:
      response = self.client.post("/status/", json=status)
      assert response.status_code == 201

    # GET should return the latest update
    response = self.client.get(f"/status/{device_id}")
    assert response.status_code == 200

    status = response.json()
    assert status["device_id"] == device_id
    assert status["battery_level"] == 30
    assert status["rssi"] == -20
    assert status["online"] == False

  def test_get_latest_status_same_day(self):
    """tests GET returns latest status for a device with multiple updates on the same day"""
    device_id = "test-sensor-2"

    statuses = [
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T11:00:00Z",
        "battery_level": 85,
        "rssi": -50,
        "online": True,
      },
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T15:11:00Z",  # latest update (expected return)
        "battery_level": 30,
        "rssi": -20,
        "online": False,
      },
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T11:30:00Z",
        "battery_level": 100,
        "rssi": -30,
        "online": True,
      },
    ]

    for status in statuses:
      response = self.client.post("/status/", json=status)
      assert response.status_code == 201

    # GET should return the latest update
    response = self.client.get(f"/status/{device_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["device_id"] == device_id
    assert data["battery_level"] == 30
    assert data["rssi"] == -20
    assert data["online"] == False

  def test_get_latest_status_same_hour(self):
    """tests GET returns latest status for a device with multiple updates within the same hour"""
    device_id = "test-sensor-3"

    statuses = [
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T14:00:00Z",
        "battery_level": 85,
        "rssi": -50,
        "online": True,
      },
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T14:23:00Z",  # latest update (expected return)
        "battery_level": 30,
        "rssi": -20,
        "online": False,
      },
      {
        "device_id": device_id,
        "timestamp": "2025-06-24T14:10:00Z",
        "battery_level": 100,
        "rssi": -30,
        "online": True,
      },
    ]

    for status in statuses:
      response = self.client.post("/status/", json=status)
      assert response.status_code == 201

    # GET should return the latest update
    response = self.client.get(f"/status/{device_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["device_id"] == device_id
    assert data["battery_level"] == 30
    assert data["rssi"] == -20
    assert data["online"] == False

  """
  /status/summary TESTS
  """

  def test_get_summary(self):
    """test GET /status/summary/ endpoint"""
    devices = [
      {
        "device_id": "device-1",
        "timestamp": "2025-06-24T14:00:00Z",
        "battery_level": 80,
        "rssi": -50,
        "online": True,
      },
      {
        "device_id": "device-2",
        "timestamp": "2025-06-24T14:05:00Z",
        "battery_level": 60,
        "rssi": -65,
        "online": False,
      },
    ]

    for device in devices:
        self.client.post("/status/", json=device)

    response = self.client.get("/status/summary/")
    assert response.status_code == 200
    summary_data = response.json()
    assert len(summary_data) == 2

    for d in summary_data:
      if d["device_id"] == "device-1":
        assert "last_update" in d
        assert "rssi" not in d
        assert d["battery_level"] == 80
        assert d["online"] == True
      else:
        assert d["device_id"] == "device-2"
        assert "last_update" in d
        assert "rssi" not in d
        assert d["battery_level"] == 60
        assert d["online"] == False

  def test_error_handling(self):
    """test API error responses"""

    response = self.client.get("/status/nonexistent-device-id")
    assert response.status_code == 404

    """test validation error"""
    invalid_input = {
      "device_id": "badinput-1",
      "timestamp": "2025-06-24T14:00:00Z",
      "battery_level": 150,  # invalid battery_level
      "rssi": -60,
      "online": True,
    }
    response = self.client.post("/status/", json=invalid_input)
    assert (
      response.status_code == 422
    )


if __name__ == "__main__":
  unittest.main()
