from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_secret
from app.db.database import SessionLocal
from app.models import User

def main():
    db: Session = SessionLocal()
    try:
        email = settings.bootstrap_admin_email.lower()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Bootstrap admin already exists: {email}")
            return
        user = User(email=email, full_name="Rice Age Super Admin", password_hash=hash_secret(settings.bootstrap_admin_password), role="SUPER_ADMIN", department_id=None)
        db.add(user); db.commit()
        print(f"Created Super Admin: {email}")
        print("Change the bootstrap password after first login and do not use the development default in production.")
    finally:
        db.close()

if __name__ == "__main__": main()
