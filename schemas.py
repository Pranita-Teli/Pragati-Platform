from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    full_name: str
    pin_code: str
    role: str
    jurisdiction_lgd_code: str

class UserCreate(UserBase):
    cryptographic_ekyc_token: str

class UserResponse(UserBase):
    id: int
    access_status: str

    class Config:
        from_attributes = True

class ElectLeaderRequest(BaseModel):
    full_name: str
    pin_code: str
    cryptographic_ekyc_token: str
    target_lgd_code: str

class TransactionDetail(BaseModel):
    timestamp: str
    type: str  # 'collection' or 'disbursement'
    amount: float
    details: str
    authorized_by_user_id: int

class BudgetLedgerResponse(BaseModel):
    id: int
    jurisdiction_lgd_code: str
    total_collected: float
    total_disbursed: float
    transaction_history: List[TransactionDetail]

    class Config:
        from_attributes = True

class GrievanceBase(BaseModel):
    description: str
    category: str
    gps_latitude: float
    gps_longitude: float
    lgd_ward_code: str

class GrievanceResponse(GrievanceBase):
    ticket_id: int
    citizen_id: int
    status: str
    upvote_count: int
    initial_photo: Optional[str] = None
    completion_photo: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
