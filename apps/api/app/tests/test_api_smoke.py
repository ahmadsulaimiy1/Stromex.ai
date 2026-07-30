"""End-to-end smoke tests through the real FastAPI app + real Postgres test
database, exercising the HTTP layer, auth, and persistence together — a level
above the unit tests, catching wiring mistakes unit tests can't see."""


def _register_and_login(client, email: str, password: str = "correcthorsebattery") -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert resp.status_code == 201, resp.text

    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_register_login_me(app_client, random_email, in_memory_qdrant):
    token = _register_and_login(app_client, random_email)
    resp = app_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == random_email


def test_duplicate_registration_is_rejected(app_client, random_email, in_memory_qdrant):
    _register_and_login(app_client, random_email)
    resp = app_client.post(
        "/api/v1/auth/register",
        json={"email": random_email, "password": "correcthorsebattery", "display_name": "Dup"},
    )
    assert resp.status_code == 409


def test_unauthenticated_request_is_rejected(app_client):
    resp = app_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_chat_persists_conversation_and_message(app_client, random_email, in_memory_qdrant):
    token = _register_and_login(app_client, random_email)
    headers = {"Authorization": f"Bearer {token}"}

    resp = app_client.post(
        "/api/v1/chat", json={"message": "Hello StromeX", "mode": "general"}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["message"]["role"] == "assistant"
    conversation_id = body["conversation_id"]

    resp = app_client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=headers)
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_non_admin_cannot_reach_admin_routes(app_client, random_email, in_memory_qdrant):
    token = _register_and_login(app_client, random_email)
    resp = app_client.get("/api/v1/admin/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_book_create_chapter_and_pdf_export(app_client, random_email, in_memory_qdrant):
    token = _register_and_login(app_client, random_email)
    headers = {"Authorization": f"Bearer {token}"}

    resp = app_client.post(
        "/api/v1/books",
        json={"title": "Test Book", "author_name": "Author", "language": "en"},
        headers=headers,
    )
    assert resp.status_code == 201
    book_id = resp.json()["id"]

    resp = app_client.post(
        f"/api/v1/books/{book_id}/chapters",
        json={"title": "Chapter One", "order_index": 0, "content_markdown": "Hello **world**"},
        headers=headers,
    )
    assert resp.status_code == 201

    resp = app_client.get(f"/api/v1/books/{book_id}/export.pdf", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"


def test_quran_plan_creation_and_review_flow(app_client, random_email, in_memory_qdrant):
    token = _register_and_login(app_client, random_email)
    headers = {"Authorization": f"Bearer {token}"}

    resp = app_client.post(
        "/api/v1/quran/plans",
        json={
            "title": "Test plan",
            "plan_type": "memorization",
            "surah_start": 114,
            "ayah_start": 1,
            "surah_end": 114,
            "ayah_end": 6,
            "daily_target_ayahs": 3,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    plan_id = resp.json()["id"]

    resp = app_client.get(f"/api/v1/quran/plans/{plan_id}/due", headers=headers)
    assert resp.status_code == 200
    due_items = resp.json()
    assert len(due_items) == 2  # 6 ayahs / 3 per chunk

    resp = app_client.post(
        "/api/v1/quran/review",
        json={"item_id": due_items[0]["id"], "grade": 5},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["repetitions"] == 1
