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
