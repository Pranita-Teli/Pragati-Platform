import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Setup Database directory
DB_DIR = r"C:\Users\PRANITA TELI\.gemini\antigravity\scratch\pragati\data"
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'pragati.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class State(Base):
    __tablename__ = "states"
    code = Column(String, primary_key=True)  # LGD State Code
    name = Column(String, nullable=False)
    districts = relationship("District", back_populates="state")

class District(Base):
    __tablename__ = "districts"
    code = Column(String, primary_key=True)  # LGD District Code
    name = Column(String, nullable=False)
    state_code = Column(String, ForeignKey("states.code"), nullable=False)
    state = relationship("State", back_populates="districts")
    blocks = relationship("Block", back_populates="district")

class Block(Base):
    __tablename__ = "blocks"
    code = Column(String, primary_key=True)  # LGD Block Code
    name = Column(String, nullable=False)
    district_code = Column(String, ForeignKey("districts.code"), nullable=False)
    district = relationship("District", back_populates="blocks")
    gps = relationship("GramPanchayat", back_populates="block")

class GramPanchayat(Base):
    __tablename__ = "gram_panchayats"
    code = Column(String, primary_key=True)  # LGD GP Code
    name = Column(String, nullable=False)
    block_code = Column(String, ForeignKey("blocks.code"), nullable=False)
    block = relationship("Block", back_populates="gps")
    wards = relationship("Ward", back_populates="gp")

class Ward(Base):
    __tablename__ = "wards"
    code = Column(String, primary_key=True)  # LGD Ward Code
    name = Column(String, nullable=False)
    gp_code = Column(String, ForeignKey("gram_panchayats.code"), nullable=False)
    gp = relationship("GramPanchayat", back_populates="wards")
    grievances = relationship("Grievance", back_populates="ward")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    cryptographic_ekyc_token = Column(String, unique=True, nullable=False)
    pin_code = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'Citizen', 'Politician', 'Admin'
    jurisdiction_lgd_code = Column(String, nullable=True)  # Can be GP or Ward code depending on role
    access_status = Column(String, default="Active")  # 'Active', 'Revoked'
    grievances = relationship("Grievance", back_populates="citizen")

class BudgetLedger(Base):
    __tablename__ = "budget_ledgers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    jurisdiction_lgd_code = Column(String, unique=True, nullable=False)
    total_collected = Column(Float, default=0.0)
    total_disbursed = Column(Float, default=0.0)
    transaction_history = Column(Text, default="[]")  # JSON string of transactions

    def add_transaction(self, tx_type: str, amount: float, details: str, user_id: int):
        history = json.loads(self.transaction_history or "[]")
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": tx_type,
            "amount": amount,
            "details": details,
            "authorized_by_user_id": user_id
        })
        self.transaction_history = json.dumps(history)

class Grievance(Base):
    __tablename__ = "grievances"
    ticket_id = Column(Integer, primary_key=True, autoincrement=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # 'Roads', 'Water', 'Sanitation', 'Electricity', etc.
    gps_latitude = Column(Float, nullable=False)
    gps_longitude = Column(Float, nullable=False)
    lgd_ward_code = Column(String, ForeignKey("wards.code"), nullable=False)
    status = Column(String, default="Logged")  # 'Logged', 'Disbursed', 'Completed'
    upvote_count = Column(Integer, default=1)
    initial_photo = Column(String, nullable=True)
    completion_photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citizen = relationship("User", back_populates="grievances")
    ward = relationship("Ward", back_populates="grievances")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Seed LGD Hierarchy if empty
    if db.query(State).count() == 0:
        # State: Maharashtra (Code: 27)
        mh = State(code="27", name="Maharashtra")
        db.add(mh)
        
        # District: Pune (Code: 521)
        pune = District(code="521", name="Pune", state_code="27")
        db.add(pune)
        
        # Block: Haveli (Code: 4215)
        haveli = Block(code="4215", name="Haveli", district_code="521")
        db.add(haveli)
        
        # Gram Panchayat: Wagholi (Code: 187654)
        wagholi = GramPanchayat(code="187654", name="Wagholi Gram Panchayat", block_code="4215")
        db.add(wagholi)
        
        # Wards (Wagholi Ward 1 to 3)
        w1 = Ward(code="2752101", name="Wagholi Ward 1", gp_code="187654")
        w2 = Ward(code="2752102", name="Wagholi Ward 2", gp_code="187654")
        w3 = Ward(code="2752103", name="Wagholi Ward 3", gp_code="187654")
        db.add_all([w1, w2, w3])
        
        # Default Ledger
        ledger = BudgetLedger(
            jurisdiction_lgd_code="187654",  # GP Level Ledger
            total_collected=5000000.0,
            total_disbursed=1200000.0,
            transaction_history=json.dumps([
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "collection",
                    "amount": 5000000.0,
                    "details": "Central DPI Grant Allocation FY2026-27",
                    "authorized_by_user_id": 1
                },
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "disbursement",
                    "amount": 1200000.0,
                    "details": "Wagholi Road repair fund release",
                    "authorized_by_user_id": 2
                }
            ])
        )
        db.add(ledger)
        
        # Default Users
        admin = User(
            full_name="Rajesh Kumar",
            cryptographic_ekyc_token="ekyc_hash_admin_12345",
            pin_code="412207",
            role="Admin",
            jurisdiction_lgd_code="27",  # State Admin
            access_status="Active"
        )
        politician = User(
            full_name="MLA Sanjay Deshmukh",
            cryptographic_ekyc_token="ekyc_hash_pol_67890",
            pin_code="412207",
            role="Politician",
            jurisdiction_lgd_code="187654",  # Gram Panchayat Code (Wagholi)
            access_status="Active"
        )
        citizen = User(
            full_name="Amit Sharma",
            cryptographic_ekyc_token="ekyc_hash_cit_11223",
            pin_code="412207",
            role="Citizen",
            jurisdiction_lgd_code="2752101",  # Ward 1 Code
            access_status="Active"
        )
        db.add_all([admin, politician, citizen])
        
        db.commit()
    db.close()
