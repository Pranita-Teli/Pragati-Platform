import os
import shutil
import math
import json
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import get_db, init_db, User, Grievance, BudgetLedger, Ward, GramPanchayat, State, District, Block
from backend.schemas import ElectLeaderRequest, UserResponse, BudgetLedgerResponse
from backend.security import hash_ekyc_token
from backend.cv_verifier import verify_construction_pattern
from backend.pdf_generator import generate_audit_pdf

app = FastAPI(title="PRAGATI Backend API", version="1.0.0")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = r"C:\Users\PRANITA TELI\/.gemini/antigravity/scratch/pragati/data/uploads"
REPORT_DIR = r"C:\Users\PRANITA TELI\/.gemini/antigravity/scratch/pragati/data/reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

@app.on_event("startup")
def startup_event():
    init_db()

# Haversine formula to compute distance in meters
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

# ----------------- Governance Core Endpoints -----------------

@app.post("/api/v1/governance/elect-leader")
def elect_leader(payload: ElectLeaderRequest, db: Session = Depends(get_db)):
    """
    Endpoint for Democratic Succession:
    Automatically search for any existing active politician handling that exact LGD jurisdiction code,
    change their Access_Status to 'Revoked', invalidate session tokens, and provision a new 'Active' profile.
    Keep historical transaction logs intact under the old leader's ID.
    """
    # Find existing active politician in the same LGD jurisdiction
    active_leaders = db.query(User).filter(
        User.jurisdiction_lgd_code == payload.target_lgd_code,
        User.role == "Politician",
        User.access_status == "Active"
    ).all()

    revoked_count = 0
    for leader in active_leaders:
        leader.access_status = "Revoked"
        # Log session invalidation/blacklisting (in production we would black-list JWTs)
        print(f"[SECURITY] Session invalidated for Revoked Leader ID: {leader.id}")
        revoked_count += 1

    # Provision new politician profile
    hashed_token = hash_ekyc_token(payload.cryptographic_ekyc_token)
    new_leader = User(
        full_name=payload.full_name,
        pin_code=payload.pin_code,
        cryptographic_ekyc_token=hashed_token,
        role="Politician",
        jurisdiction_lgd_code=payload.target_lgd_code,
        access_status="Active"
    )
    db.add(new_leader)
    db.commit()
    db.refresh(new_leader)

    return {
        "status": "success",
        "message": f"Democratic Succession executed successfully. Revoked {revoked_count} old leaders.",
        "new_leader": {
            "id": new_leader.id,
            "full_name": new_leader.full_name,
            "role": new_leader.role,
            "jurisdiction_lgd_code": new_leader.jurisdiction_lgd_code,
            "access_status": new_leader.access_status
        }
    }

# ----------------- User Management Helpers -----------------

@app.get("/api/v1/users")
def get_users(role: str = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return [{
        "id": u.id,
        "full_name": u.full_name,
        "role": u.role,
        "jurisdiction_lgd_code": u.jurisdiction_lgd_code,
        "access_status": u.access_status,
        "pin_code": u.pin_code
    } for u in users]

@app.post("/api/v1/users/create")
def create_user(
    full_name: str = Form(...),
    pin_code: str = Form(...),
    role: str = Form(...),
    jurisdiction_lgd_code: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing = db.query(User).filter(User.full_name == full_name, User.role == role).first()
    if existing:
        return existing
    
    # Generate mock token
    raw_token = f"ekyc_{role.lower()}_{len(full_name)}"
    hashed_token = hash_ekyc_token(raw_token)
    user = User(
        full_name=full_name,
        pin_code=pin_code,
        role=role,
        cryptographic_ekyc_token=hashed_token,
        jurisdiction_lgd_code=jurisdiction_lgd_code,
        access_status="Active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ----------------- Budget Ledger Endpoints -----------------

@app.get("/api/v1/budget/summary")
def get_budget_summary(db: Session = Depends(get_db)):
    """
    Returns aggregated KPI stats: Total money collected vs expended.
    """
    ledgers = db.query(BudgetLedger).all()
    total_collected = sum(l.total_collected for l in ledgers)
    total_disbursed = sum(l.total_disbursed for l in ledgers)
    return {
        "total_collected": total_collected,
        "total_disbursed": total_disbursed,
        "net_balance": total_collected - total_disbursed
    }

@app.get("/api/v1/budget/{lgd_code}")
def get_budget_ledger(lgd_code: str, db: Session = Depends(get_db)):
    ledger = db.query(BudgetLedger).filter(BudgetLedger.jurisdiction_lgd_code == lgd_code).first()
    if not ledger:
        # Create empty ledger if not found
        ledger = BudgetLedger(jurisdiction_lgd_code=lgd_code, total_collected=1000000.0, total_disbursed=0.0)
        db.add(ledger)
        db.commit()
        db.refresh(ledger)
    
    history = json.loads(ledger.transaction_history or "[]")
    return {
        "id": ledger.id,
        "jurisdiction_lgd_code": ledger.jurisdiction_lgd_code,
        "total_collected": ledger.total_collected,
        "total_disbursed": ledger.total_disbursed,
        "transaction_history": history
    }

@app.post("/api/v1/budget/disburse")
def disburse_budget(
    lgd_code: str = Form(...),
    amount: float = Form(...),
    details: str = Form(...),
    authorized_by: int = Form(...),
    db: Session = Depends(get_db)
):
    # Verify leader authority
    user = db.query(User).filter(User.id == authorized_by).first()
    if not user or user.role != "Politician" or user.access_status != "Active":
        raise HTTPException(status_code=403, detail="Unauthorized. Active Politician profile required.")

    ledger = db.query(BudgetLedger).filter(BudgetLedger.jurisdiction_lgd_code == lgd_code).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Budget ledger for jurisdiction not found.")

    if ledger.total_collected - ledger.total_disbursed < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in budget ledger.")

    ledger.total_disbursed += amount
    ledger.add_transaction(
        tx_type="disbursement",
        amount=amount,
        details=details,
        user_id=authorized_by
    )
    db.commit()
    return {"status": "success", "total_disbursed": ledger.total_disbursed, "balance": ledger.total_collected - ledger.total_disbursed}

# ----------------- Grievance Endpoints -----------------

@app.post("/api/v1/grievance/raise")
def raise_grievance(
    citizen_id: int = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    gps_latitude: float = Form(...),
    gps_longitude: float = Form(...),
    lgd_ward_code: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Check if citizen profile is active
    citizen = db.query(User).filter(User.id == citizen_id).first()
    if not citizen or citizen.access_status != "Active":
        raise HTTPException(status_code=403, detail="Active citizen profile required.")

    # 1. Geo-fence duplicate check: within 50m radius of active complaints
    open_tickets = db.query(Grievance).filter(Grievance.status != "Completed").all()
    
    for ticket in open_tickets:
        dist = haversine_distance(gps_latitude, gps_longitude, ticket.gps_latitude, ticket.gps_longitude)
        if dist <= 50.0:
            # Prevent duplicate and increment existing ticket's upvote count
            ticket.upvote_count += 1
            db.commit()
            return {
                "status": "duplicate",
                "message": f"A duplicate complaint (TKT-{ticket.ticket_id}) exists within 50 meters. Your vote has been added.",
                "ticket_id": ticket.ticket_id,
                "upvote_count": ticket.upvote_count
            }

    # 2. Save file locally
    saved_photo_path = None
    if photo:
        filename = f"initial_{datetime.utcnow().timestamp()}_{photo.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        saved_photo_path = filepath

    # 3. Insert new grievance record
    new_ticket = Grievance(
        citizen_id=citizen_id,
        description=description,
        category=category,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        lgd_ward_code=lgd_ward_code,
        status="Logged",
        upvote_count=1,
        initial_photo=saved_photo_path
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    return {
        "status": "success",
        "ticket_id": new_ticket.ticket_id,
        "upvote_count": new_ticket.upvote_count,
        "message": "Grievance successfully logged."
    }

@app.get("/api/v1/grievances")
def get_grievances(ward_code: str = None, politician_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Grievance)
    
    if ward_code:
        query = query.filter(Grievance.lgd_ward_code == ward_code)
        
    elif politician_id:
        pol = db.query(User).filter(User.id == politician_id).first()
        if pol and pol.role == "Politician" and pol.access_status == "Active":
            # Filter wards within politician's jurisdiction
            wards = db.query(Ward).filter(Ward.gp_code == pol.jurisdiction_lgd_code).all()
            ward_codes = [w.code for w in wards]
            query = query.filter(Grievance.lgd_ward_code.in_(ward_codes))
            
    grievances = query.all()
    return [{
        "ticket_id": g.ticket_id,
        "citizen_id": g.citizen_id,
        "citizen_name": g.citizen.full_name,
        "description": g.description,
        "category": g.category,
        "gps_latitude": g.gps_latitude,
        "gps_longitude": g.gps_longitude,
        "lgd_ward_code": g.lgd_ward_code,
        "status": g.status,
        "upvote_count": g.upvote_count,
        "initial_photo": g.initial_photo,
        "completion_photo": g.completion_photo,
        "created_at": g.created_at,
        "updated_at": g.updated_at
    } for g in grievances]

# ----------------- CV Auditing & Completion Endpoints -----------------

@app.post("/api/v1/audit/verify-completion")
def verify_completion(
    ticket_id: int = Form(...),
    politician_id: int = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Advanced Image Verification:
    Runs mock computer vision pattern validation on the uploaded completion photo.
    Only proceeds to status 'Completed' if verification criteria is met.
    """
    # Check politician authority
    pol = db.query(User).filter(User.id == politician_id).first()
    if not pol or pol.role != "Politician" or pol.access_status != "Active":
        raise HTTPException(status_code=403, detail="Unauthorized. Active Politician session required.")

    ticket = db.query(Grievance).filter(Grievance.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Grievance ticket not found.")

    # Save completion photo
    filename = f"completion_{datetime.utcnow().timestamp()}_{photo.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
    
    # Run simulated CV texture patterns checking
    success, score, report = verify_construction_pattern(ticket.initial_photo, filepath)
    
    if not success:
        # Invalidate / reject completion status updates
        raise HTTPException(
            status_code=422,
            detail=f"CV Auditing Failed (Score: {score*100}%): Asphalt/concrete pattern not matching engineering standards. {report}"
        )

    # Update database status
    ticket.completion_photo = filepath
    ticket.status = "Completed"
    db.commit()

    return {
        "status": "success",
        "message": "Grievance completion successfully verified by CV pipeline and closed.",
        "cv_score": score,
        "analysis_report": report
    }

# ----------------- Auditing PDF Reports Endpoints -----------------

@app.get("/api/v1/audit/report/{lgd_code}")
def download_audit_report(lgd_code: str, db: Session = Depends(get_db)):
    """
    Build administrative report PDF capturing complaints, budgets and status rates.
    """
    # Fetch data based on GP code
    gp = db.query(GramPanchayat).filter(GramPanchayat.code == lgd_code).first()
    if not gp:
        raise HTTPException(status_code=404, detail="Gram Panchayat not found.")

    # Get budget ledger
    ledger = db.query(BudgetLedger).filter(BudgetLedger.jurisdiction_lgd_code == lgd_code).first()
    budget_data = {
        "total_collected": ledger.total_collected if ledger else 0.0,
        "total_disbursed": ledger.total_disbursed if ledger else 0.0
    }

    # Fetch grievances in wards of this Gram Panchayat
    wards = db.query(Ward).filter(Ward.gp_code == lgd_code).all()
    ward_codes = [w.code for w in wards]
    grievances_records = db.query(Grievance).filter(Grievance.lgd_ward_code.in_(ward_codes)).all()
    
    grievances_list = [{
        "ticket_id": g.ticket_id,
        "category": g.category,
        "description": g.description,
        "status": g.status,
        "upvote_count": g.upvote_count
    } for g in grievances_records]

    # Generate PDF
    filepath = generate_audit_pdf(
        lgd_code=lgd_code,
        ward_name=gp.name,
        grievances=grievances_list,
        budget=budget_data,
        output_dir=REPORT_DIR
    )

    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/pdf"
    )
