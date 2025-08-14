from flask_app import app


def test_homepage_contains_brand_and_hero():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    assert "New P" in html
    assert "Добро пожаловать" in html


def test_about_page_exists():
    client = app.test_client()
    response = client.get("/about")
    assert response.status_code == 200
    assert "О проекте" in response.data.decode()


def test_healthz_ok():
    client = app.test_client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.is_json
    assert response.json == {"status": "ok"}