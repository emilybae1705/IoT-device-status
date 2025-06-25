import unittest
from pydantic import ValidationError
from datetime import datetime, timezone

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import DeviceStatus, DeviceStatusInput, DeviceStatusUpdate


class DeviceStatusValidation(unittest.TestCase):
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
        try:
            DeviceStatusInput()
            assert False, "Missing all required fields, should raise ValidationError"
        except ValidationError:
            pass

    def test_battery_level(self):
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

        try:
            DeviceStatusInput(
                device_id="badtest-1",
                timestamp=datetime.now(),
                battery_level=-50,
                rssi=50,
                online=False,
            )
            assert False, "Should raise validation error for battery_level=-50"
        except ValidationError:
            pass

        try:
            DeviceStatusInput(
                device_id="badtest-2",
                timestamp=datetime.now(),
                battery_level=120,
                rssi=50,
                online=True,
            )
            assert False, "Should raise validation error for battery_level=120"
        except ValidationError:
            pass

    def test_partial_update(self):
        """test partial update logic"""
        update = DeviceStatusUpdate(battery_level=70, online=False)
        assert update.battery_level == 70
        assert update.online == False
        assert update.rssi == None  # rssi not provided in update

        try:
            DeviceStatusUpdate(battery_level=130)
            assert False, "Should raise validation error for battery_level=130"
        except ValidationError:
            pass


if __name__ == "__main__":
    unittest.main()
