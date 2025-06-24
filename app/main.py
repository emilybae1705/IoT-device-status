from fastapi import FastAPI, APIRouter, HTTPException, Depends
from sqlmodel import Session, select, func
from models import DeviceStatus, DeviceStatusInput, DeviceStatusUpdate, SummaryItem
from database import get_session, create_DB
from contextlib import asynccontextmanager
import uvicorn

# runs on application startup
# once session ends, cleans up and shuts down
@asynccontextmanager
def lifespan(app: FastAPI):
  create_DB()
  yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
  return "Server is running..."

router = APIRouter(
  prefix="/status",
  tags=["status"],
  responses={
    404: {"description": "Not found"},
    201: {"description": "Successfully created"},
  },
)

@router.post("/", response_model=DeviceStatus, status_code=201, tags=["status"])
def create_status(status: DeviceStatusInput, session: Session = Depends(get_session)):
  status = DeviceStatus(**status.model_dump())
  session.add(status)
  session.commit()
  session.refresh(status)
  return status

@router.get("/")
def get_all_status(session: Session = Depends(get_session)):
    return session.exec(select(DeviceStatus)).all()

@router.get("/summary/", response_model=list[SummaryItem])
def get_summary(session: Session = Depends(get_session)):
  latest_statuses = (
    select(DeviceStatus.device_id, func.max(DeviceStatus.timestamp).label("max_timestamp"))
    .group_by(DeviceStatus.device_id)
    .subquery()
  )
  query = select(DeviceStatus).join(
    latest_statuses,
    (DeviceStatus.device_id == latest_statuses.c.device_id) &
    (DeviceStatus.timestamp == latest_statuses.c.max_timestamp),
  )
  results = session.exec(query).all()
  if not results:
    raise HTTPException(status_code=404, detail="Summary cannot be generated")

  return [
    SummaryItem(
      device_id=device.device_id,
      last_update=device.timestamp,
      battery_level=device.battery_level,
      online=device.online,
    )
    for device in results
  ]
    
@router.get("/{device_id}", response_model=DeviceStatus)
def get_latest_status(device_id: str, session: Session = Depends(get_session)):
  query = (
      select(DeviceStatus)
      .where(DeviceStatus.device_id == device_id)
      .order_by(DeviceStatus.timestamp.desc())
  )
  result = session.exec(query).first()
  if not result:
      raise HTTPException(status_code=404, detail="Device not found")
  return result

@router.patch("/{device_id}", response_model=DeviceStatus)
def update_status(device_id: str, update: DeviceStatusUpdate, session: Session = Depends(get_session)):
  device = session.exec(
    select(DeviceStatus).where(DeviceStatus.device_id == device_id).first()
  )
  if not device:
    raise HTTPException(status_code=404, detail=f"No device found with device_id={device_id}")
  
  updated_status = update.model_dump(exclude_unset=True)
  for key, value in updated_status.items():
    setattr(device, key, value)
  
  session.add(device)
  session.commit()
  session.refresh(device)
  return device

def delete_status(device_id: str, session: Session = Depends(get_session)):
  device = session.exec(
    select(DeviceStatus).where(DeviceStatus.device_id == device_id).first()
  )
  if not device:
    raise HTTPException(status_code=404, detail=f"No device found with device_id={device_id}")
  
  session.delete(device)
  session.commit()
  return f"successfully deleted device {device_id}"

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
