"""Shared test helpers: authenticated HTTP clients.

Auth is fail-closed — there is no anonymous mode — so API tests that used to
flip AUTH_REQUIRED off now sign in as a seeded admin instead.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

ADMIN_EMAIL = "audit-admin@example.com"
ADMIN_PASSWORD = "audit-admin-password-123"


def authed_client(role: str = "ADMIN"):
    """TestClient logged in as a seeded user, bearer pre-attached."""
    from fastapi.testclient import TestClient
    import main
    from app.db.session import SessionLocal
    from app.models import User, RoleEnum
    from app.core.security import get_password_hash
    from app.core import ratelimit

    main.Base.metadata.create_all(bind=main.engine)
    db = SessionLocal()
    # Drop rows left by older runs whose emails no longer validate — one bad
    # row 500s every list endpoint that serializes UserResponse.
    for stale in db.query(User).filter(User.email.like("%@test.local")).all():
        db.delete(stale)
    db.commit()
    user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if user is None:
        user = User(
            email=ADMIN_EMAIL,
            name="Audit Admin",
            password_hash=get_password_hash(ADMIN_PASSWORD),
            role=RoleEnum.ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
    else:
        user.role = RoleEnum.ADMIN if role == "ADMIN" else RoleEnum.SECURITY_OFFICER
        user.is_active = True
        user.password_hash = get_password_hash(ADMIN_PASSWORD)
        db.commit()
    db.close()

    ratelimit._hits.clear()
    client = TestClient(main.app)
    res = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
