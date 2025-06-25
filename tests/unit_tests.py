import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import DeviceStatus, DeviceStatusInput, DeviceStatusUpdate


class TestDeviceStatusValidation:
    """tests core input validation logic"""

    def test_valid_status_input(self):
        """tests creating valid device status"""
        status = DeviceStatusInput(
            device_id="sensor-abc-123",
            timestamp="2025-06-09T14:00:00Z",
            battery_level=76,
            rssi=-60,
            online=True,
        )
        assert status.device_id == "sensor-abc-123"
        assert isinstance(status.timestamp, datetime)
        assert status.timestamp == datetime(2025, 6, 9, 14, 0, 0, tzinfo=timezone.utc)
        assert status.battery_level == 76
        assert status.rssi == -60
        assert status.online == True

    def test_required_fields(self):
        """tests required fields are all inputted"""
        with pytest.raises(ValidationError):
            DeviceStatusInput()

    def test_battery_level_valid_range(self):
        """tests battery level must be between 0-100 inclusive"""

        battery_0 = DeviceStatusInput(
            device_id="test-1",
            timestamp=datetime.now(),
            battery_level=0,
            rssi=50,
            online=False,
        )
        assert battery_0.battery_level == 0

        battery_100 = DeviceStatusInput(
            device_id="test-2",
            timestamp=datetime.now(),
            battery_level=100,
            rssi=50,
            online=True,
        )
        assert battery_100.battery_level == 100

    def test_battery_level_invalid_low(self):
        """tests battery level validation for values below 0"""
        with pytest.raises(ValidationError):
            DeviceStatusInput(
                device_id="badtest-1",
                timestamp=datetime.now(),
                battery_level=-50,
                rssi=50,
                online=False,
            )

    def test_battery_level_invalid_high(self):
        """tests battery level validation for values above 100"""
        with pytest.raises(ValidationError):
            DeviceStatusInput(
                device_id="badtest-2",
                timestamp=datetime.now(),
                battery_level=120,
                rssi=50,
                online=True,
            )

    def test_partial_update_valid(self):
        """test partial update logic with valid data"""
        update = DeviceStatusUpdate(battery_level=70, online=False)
        assert update.battery_level == 70
        assert update.online == False

    def test_partial_update_invalid_battery(self):
        """test partial update validation for invalid battery level"""
        with pytest.raises(ValidationError):
            DeviceStatusUpdate(battery_level=130)

    def test_timestamp_edge_cases(self):
        """test various timestamp format edge cases"""

        valid_timestamps = [
            "2025-06-09T14:00:00Z",
            "2025-06-09T14:00:00+00:00",
            "2025-06-09T14:00:00.123Z",
            "2025-06-09T14:00:00.123456Z",
        ]

        for timestamp_str in valid_timestamps:
            status = DeviceStatusInput(
                device_id="test-timestamp-valid",
                timestamp=timestamp_str,
                battery_level=50,
                rssi=-60,
                online=True,
            )
            assert isinstance(status.timestamp, datetime)

        invalid_timestamps = [
            "2025-06-09T7:00:00Z",  # Single digit hour (should be 07)
            "2025-13-01T14:00:00Z",  # Invalid month (13)
            "2025-06-32T14:00:00Z",  # Invalid day (32)
            "2025-06-09T25:00:00Z",  # Invalid hour (25)
            "2025-06-09T14:60:00Z",  # Invalid minute (60)
            "2025-06-09T14:00:60Z",  # Invalid second (60)
            "invalid-timestamp",  # Completely invalid
            "14:00:00",  # Missing date
        ]

        for timestamp_str in invalid_timestamps:
            with pytest.raises(ValidationError):
                DeviceStatusInput(
                    device_id="test-timestamp-invalid",
                    timestamp=timestamp_str,
                    battery_level=50,
                    rssi=-60,
                    online=True,
                )
