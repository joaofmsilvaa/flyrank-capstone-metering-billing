import sys
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.db.models import Plan, Tenant, Subscription, PlanType

def seed_database():
    print("Seeding the database...")
    
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()

    try:
        plan_free = db.query(Plan).filter_by(id="plan_free").first()
        if not plan_free:
            plan_free = Plan(
                id="plan_free",
                name=PlanType.FREE,
                max_api_calls_per_month=1000,
                max_tokens_per_month=100000
            )
            db.add(plan_free)
            print("  └─ Plan 'FREE' created.")

        plan_pro = db.query(Plan).filter_by(id="plan_pro").first()
        if not plan_pro:
            plan_pro = Plan(
                id="plan_pro",
                name=PlanType.PRO,
                max_api_calls_per_month=50000,
                max_tokens_per_month=5000000
            )
            db.add(plan_pro)
            print("  └─ Plan 'PRO' created.")

        db.commit()

        tenant_acme = db.query(Tenant).filter_by(id="tenant_acme").first()
        if not tenant_acme:
            tenant_acme = Tenant(
                id="tenant_acme", 
                name="Acme Corporation (Free Plan)"
            )
            db.add(tenant_acme)
            db.commit()

            sub_acme = Subscription(
                id="sub_acme_free",
                tenant_id="tenant_acme",
                plan_id="plan_free",
                status="active"
            )
            db.add(sub_acme)
            db.commit()
            print("  └─ Tenant 'tenant_acme' (Free) created with a active subscription.")

        tenant_globex = db.query(Tenant).filter_by(id="tenant_globex").first()
        if not tenant_globex:
            tenant_globex = Tenant(
                id="tenant_globex", 
                name="Globex Inc (Pro Plan)"
            )
            db.add(tenant_globex)
            db.commit()

            sub_globex = Subscription(
                id="sub_globex_pro",
                tenant_id="tenant_globex",
                plan_id="plan_pro",
                status="active"
            )
            db.add(sub_globex)
            db.commit()
            print("  └─ Tenant 'tenant_globex' (Pro) created with active subscription.")

        print("Seed successfully concluded!")

    except Exception as e:
        print(f"Error seeding the database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()