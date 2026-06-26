def test_health(client):
    assert client.get("/health").status_code == 200


def test_submit_requires_auth(client):
    resp = client.post("/submit", json={"text": "hello"})
    assert resp.status_code == 401


def test_submit_requires_content(client, auth):
    resp = client.post("/submit", json={}, headers=auth)
    assert resp.status_code == 400


def test_submit_classifies_text(client, auth):
    resp = client.post("/submit", json={"text": "A short human note about my day.", "creator_id": "u1"}, headers=auth)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "content_id" in body
    assert body["attribution"] in {"likely_human", "uncertain", "likely_ai"}
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["label"]


def test_submit_image_upload(client, auth):
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buf, format="PNG")
    buf.seek(0)

    resp = client.post(
        "/submit",
        data={"creator_id": "u-img", "file": (buf, "art.png")},
        headers=auth,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["source"] == "image"
    assert "content_id" in body


def test_appeal_flow(client, auth):
    submitted = client.post("/submit", json={"text": "Some content here.", "creator_id": "u2"}, headers=auth).get_json()
    cid = submitted["content_id"]

    resp = client.post("/appeal", json={"content_id": cid, "reasoning": "This is my original work."}, headers=auth)
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "under_review"


def test_appeal_unknown_content(client, auth):
    resp = client.post("/appeal", json={"content_id": "does-not-exist", "reasoning": "x"}, headers=auth)
    assert resp.status_code == 404


def test_log_endpoint(client, auth):
    client.post("/submit", json={"text": "logged content", "creator_id": "u3"}, headers=auth)
    resp = client.get("/log", headers=auth)
    assert resp.status_code == 200
    assert len(resp.get_json()["entries"]) >= 1


def test_dashboard_metrics(client, auth):
    client.post("/submit", json={"text": "dashboard content", "creator_id": "u4"}, headers=auth)
    resp = client.get("/dashboard", headers=auth)
    assert resp.status_code == 200
    metrics = resp.get_json()
    assert metrics["total_submissions"] >= 1
    assert "appeal_rate" in metrics


def test_certificate_flow(client, auth):
    client.post("/certify", json={"creator_id": "verified-creator"}, headers=auth)
    resp = client.post("/submit", json={"text": "content", "creator_id": "verified-creator"}, headers=auth)
    cert = resp.get_json()["certificate"]
    assert cert["verified_human"] is True
