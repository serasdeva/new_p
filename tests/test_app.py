from flask_app import app


def test_index_renders_html():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode()
    assert "Фотостудия" in html
    assert "Портфолио" in html


def test_healthz():
    client = app.test_client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.data.decode() == "ok"