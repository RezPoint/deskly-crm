from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models import User, Tenant
from app.core.security import hash_password

def create_user():
    db = SessionLocal()
    # Создаем тенерта, если его нет
    tenant = db.query(Tenant).filter(Tenant.id == 1).first()
    if not tenant:
        tenant = Tenant(id=1, name="Default", slug="default")
        db.add(tenant)
        db.commit()

    # Создаем пользователя
    user = db.query(User).filter(User.email == "owner@example.com").first()
    if not user:
        user = User(
            email="owner@example.com",
            password_hash=hash_password("password123"),
            tenant_id=1,
            role="owner"
        )
        db.add(user)
        db.commit()
        print("✅ Пользователь owner@example.com создан!")
    else:
        # Обновим пароль на всякий случай
        user.password_hash = get_password_hash("password123")
        db.commit()
        print("ℹ️ Пользователь уже существует, пароль обновлен.")
    db.close()

if __name__ == "__main__":
    create_user()
