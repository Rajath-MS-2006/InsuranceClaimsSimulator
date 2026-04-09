import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from tinydb import TinyDB, Query

# SQLite for Structured Policy Rules
SQLITE_URL = "sqlite:///./health_claims.db"
Base = declarative_base()

class DBPolicyRule(Base):
    __tablename__ = "policy_rules"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    cap_amount = Column(Float, nullable=True)
    copay_percentage = Column(Float, nullable=True)
    is_excluded = Column(Boolean, default=False)
    raw_clause = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'patient', 'hospital', 'insurance'

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("✅ SQLite connected (Policies).")

# TinyDB for Extracted Documents & Claims
BILLS_DB_PATH = "./claims_db.json"
tinydb_client = TinyDB(BILLS_DB_PATH)
claims_table = tinydb_client.table('claims')
print("✅ TinyDB connected (Claims).")

def save_rule_to_pg(rule_data):
    try:
        db_sess = SessionLocal()
        db_rule = DBPolicyRule(**rule_data)
        db_sess.add(db_rule)
        db_sess.commit()
        db_sess.close()
        return True
    except:
        return False

def save_claim_to_mongo(claim_data: dict):
    # Using TinyDB instead of MongoDB
    try:
        claims_table.insert(claim_data)
        return True
    except:
        return False
        
def get_all_claims():
    try:
        all_claims = claims_table.all()
        # Ensure we return ids correctly, injecting _id for compatibility
        for c in all_claims:
            c['_id'] = str(c.doc_id)
        return all_claims
    except:
        return []
