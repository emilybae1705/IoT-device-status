from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class DeviceStatus(SQLModel):
  id: Optional[int] = Field(primary_key=True, index=True)
  device_id: str = Field(index=True)
  timestamp: datetime
  battery_level: int = Field(ge=0, le=100)
  rssi: int
  online: bool
  
class DeviceStatusCreate(SQLModel):
  device_id: str
  timestamp: datetime
  battery_level: int = Field(ge=0, le=100)
  rssi: int
  online: bool
  
class SummaryItem(SQLModel):
  device_id: str
  last_update: datetime
  battery_level: int = Field(ge=0, le=100)
  online: bool
