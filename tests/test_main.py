from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.json() == {"Hello": "World"}


def test_read_item():
    response = client.get("/items/1", params={"q": "test"})
    assert response.json() == {"item_id": 1, "q": "test"}
