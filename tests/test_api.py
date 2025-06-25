import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app
from app.database import get_session
from app.models import DeviceStatus

os.environ["API_KEY"] = "test-api-key"


class TestStatusAPI:
    """Integration Tests for status API"""

    @pytest.fixture(name="session")
    def session_fixture(self):
        """pytest fixture for creating engine and session instance before each test"""

        self.engine = create_engine(
            "sqlite://",
            connect_args={
                "check_same_thread": False
            },  # enables accessing database from different threads
            poolclass=StaticPool,  # tells SQLite we want to use the same in-memory database from different threads
        )
        SQLModel.metadata.create_all(self.engine)

        with Session(self.engine) as session:
            yield session

    @pytest.fixture(name="client")
    def client_fixture(self, session: Session):
        """pytest fixture for TestClient setup before each test
        dependency: session fixture
        """

        def get_test_session():
            return session

        app.dependency_overrides[get_session] = get_test_session

        self.client = TestClient(app)
        yield self.client
        app.dependency_overrides.clear()  # teardown after every test

    @pytest.fixture(name="auth_headers")
    def auth_headers_fixture(self):
        """pytest fixture for authentication headers used in all tests"""
        return {"x-api-key": "test-api-key"}

    """
    /status/ TESTS
    """

    def test_create_and_get_status(self, client: TestClient, auth_headers):
        status = {
            "device_id": "sensor-abc-123",
            "timestamp": "2025-06-09T14:00:00Z",
            "battery_level": 76,
            "rssi": -60,
            "online": True,
        }

        # POST /status/
        response = self.client.post("/status/", json=status, headers=auth_headers)
        data = response.json()
        assert response.status_code == 201
        assert data["device_id"] == "sensor-abc-123"
        assert data["battery_level"] == 76
        assert data["rssi"] == -60
        assert data["online"] == True

        # GET /status/sensor-abc-123
        response = self.client.get("/status/sensor-abc-123", headers=auth_headers)
        data = response.json()
        assert response.status_code == 200
        assert data["device_id"] == "sensor-abc-123"
        assert data["battery_level"] == 76
        assert data["rssi"] == -60
        assert data["online"] == True

    def test_get_latest_status_different_dates(self, client: TestClient, auth_headers):
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
                "timestamp": "2025-06-30T07:00:00Z",  # latest update (expected return)
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
            response = self.client.post("/status/", json=status, headers=auth_headers)
            assert response.status_code == 201

        response = self.client.get(f"/status/{device_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["device_id"] == device_id
        assert data["battery_level"] == 30
        assert data["rssi"] == -20
        assert data["online"] == False

    def test_get_latest_status_same_day(self, client: TestClient, auth_headers):
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
            response = self.client.post("/status/", json=status, headers=auth_headers)
            assert response.status_code == 201

        response = self.client.get(f"/status/{device_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["device_id"] == device_id
        assert data["battery_level"] == 30
        assert data["rssi"] == -20
        assert data["online"] == False

    def test_get_latest_status_same_hour(self, client: TestClient, auth_headers):
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
            response = self.client.post("/status/", json=status, headers=auth_headers)
            assert response.status_code == 201

        response = self.client.get(f"/status/{device_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["device_id"] == device_id
        assert data["battery_level"] == 30
        assert data["rssi"] == -20
        assert data["online"] == False

    """
    /status/summary TESTS
    """

    def test_get_summary(self, client: TestClient, auth_headers):
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
            self.client.post("/status/", json=device, headers=auth_headers)

        response = self.client.get("/status/summary/", headers=auth_headers)
        assert response.status_code == 200

        summary_data = response.json()
        assert len(summary_data) == 2

        assert summary_data[0]["device_id"] == "device-1"
        assert "last_update" in summary_data[0]
        assert summary_data[0]["battery_level"] == 80
        assert summary_data[0]["online"] == True

        assert summary_data[1]["device_id"] == "device-2"
        assert "last_update" in summary_data[1]
        assert summary_data[1]["battery_level"] == 60
        assert summary_data[1]["online"] == False

    def test_error_handling(self, client: TestClient, auth_headers):
        """test API error responses"""

        response = self.client.get("/status/nonexistent-device-id", headers=auth_headers)
        assert response.status_code == 404

        """test validation error"""
        invalid_input = {
            "device_id": "badinput-1",
            "timestamp": "2025-06-24T14:00:00Z",
            "battery_level": 150,  # invalid battery_level
            "rssi": -60,
            "online": True,
        }
        response = self.client.post("/status/", json=invalid_input, headers=auth_headers)
        assert response.status_code == 422

    def test_summary_empty_database(self, client: TestClient, auth_headers):
        """test summary endpoint with no devices in database"""
        response = self.client.get("/status/summary/", headers=auth_headers)
        assert response.status_code == 404
        assert "Summary cannot be generated" in response.json()["detail"]

    def test_multiple_devices_same_timestamp(self, client: TestClient, auth_headers):
        """test behavior when multiple devices have identical timestamps"""

        same_timestamp = "2025-06-24T14:00:00Z"

        devices = [
            {
                "device_id": "device-same-time-1",
                "timestamp": same_timestamp,
                "battery_level": 80,
                "rssi": -50,
                "online": True,
            },
            {
                "device_id": "device-same-time-2",
                "timestamp": same_timestamp,
                "battery_level": 60,
                "rssi": -65,
                "online": False,
            },
            {
                "device_id": "device-same-time-3",
                "timestamp": same_timestamp,
                "battery_level": 90,
                "rssi": -40,
                "online": True,
            },
        ]

        for device in devices:
            response = self.client.post("/status/", json=device, headers=auth_headers)
            assert response.status_code == 201

        response = self.client.get("/status/summary/", headers=auth_headers)
        assert response.status_code == 200

        summary_data = response.json()
        assert len(summary_data) == 3

        for device in summary_data:
            assert device["last_update"] == same_timestamp.replace("Z", "")

        # test individual device endpoints
        for device_id in [
            "device-same-time-1",
            "device-same-time-2",
            "device-same-time-3",
        ]:
            response = self.client.get(f"/status/{device_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["timestamp"] == same_timestamp.replace("Z", "")

    def test_summary_with_many_devices(self, client: TestClient, auth_headers):
        """test summary endpoint with many devices"""

        devices = []
        for i in range(10):  # 10 devices with varying timestamps
            device = {
                "device_id": f"device-many-{i}",
                "timestamp": f"2025-06-24T14:{i:02d}:00Z",
                "battery_level": 50 + i * 5,
                "rssi": -60 - i,
                "online": i % 2 == 0,  # toggle online/offline
            }
            devices.append(device)

        for device in devices:
            response = self.client.post("/status/", json=device, headers=auth_headers)
            assert response.status_code == 201

        response = self.client.get("/status/summary/", headers=auth_headers)
        assert response.status_code == 200

        summary_data = response.json()
        assert len(summary_data) == 10

        device_ids = [d["device_id"] for d in summary_data]
        for i in range(10):
            expected_device_id = f"device-many-{i}"
            assert expected_device_id in device_ids

            device_data = next(
                d for d in summary_data if d["device_id"] == expected_device_id
            )
            assert device_data["battery_level"] == 50 + i * 5
            assert device_data["online"] == (i % 2 == 0)
            assert "last_update" in device_data

    def test_authentication(self, client: TestClient, auth_headers):
        """test API key authentication"""

        # test without API key header
        response = self.client.get("/status/summary/")
        assert response.status_code == 401
        assert "missing API key header" in response.json()["detail"]

        # test with invalid API key
        response = self.client.get(
            "/status/summary/", headers={"x-api-key": "invalid-key"}
        )
        assert response.status_code == 401
        assert "invalid API key" in response.json()["detail"]

        # test with valid API key (if API_KEY is set in environment)
        api_key = os.getenv("API_KEY")
        if api_key:
            response = self.client.get(
                "/status/summary/", headers={"x-api-key": api_key}
            )
            # either succeeds (200) or fails with 404 (no data)
            assert response.status_code in [200, 404]
        else:
            # works without header if no API key configured
            response = self.client.get("/status/summary/")
            assert response.status_code in [200, 404]
