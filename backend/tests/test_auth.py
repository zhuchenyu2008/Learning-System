from app.core.security import create_access_token, get_password_hash
from app.models.enums import UserRole
from app.models.user import User

import pytest


@pytest.mark.asyncio
async def test_login_and_me(client):
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["success"] is True
    access_token = login_payload["data"]["tokens"]["access_token"]
    refresh_token = login_payload["data"]["tokens"]["refresh_token"]
    assert access_token
    assert refresh_token

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me_payload = me_response.json()
    assert me_payload["data"]["username"] == "admin"
    assert me_payload["data"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_failures_and_me_requires_valid_token(client, session_factory):
    async with session_factory() as session:
        session.add(
            User(
                username="disabled",
                email="disabled@example.com",
                password_hash=get_password_hash("ChangeMe123!"),
                role=UserRole.VIEWER,
                is_active=False,
            )
        )
        await session.commit()

    wrong_password = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid username or password"

    disabled_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "disabled", "password": "ChangeMe123!"},
    )
    assert disabled_login.status_code == 200

    disabled_token = disabled_login.json()["data"]["tokens"]["access_token"]
    disabled_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {disabled_token}"},
    )
    assert disabled_me.status_code == 401
    assert disabled_me.json()["detail"] == "Could not validate credentials"

    missing_token = await client.get("/api/v1/auth/me")
    assert missing_token.status_code == 401

    invalid_type_token = create_access_token("admin")
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": invalid_type_token},
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_refresh_token(client):
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    refresh_token = login_response.json()["data"]["tokens"]["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()
    assert refresh_payload["success"] is True
    assert refresh_payload["data"]["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_logout_contract_is_stable(client):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["message"] == "Logged out"
