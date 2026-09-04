import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert set(activities["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_signup_adds_participant():
    email = "student@example.com"

    response = client.post("/activities/Soccer%20Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up student@example.com for Soccer Team"}
    assert email in app_module.activities["Soccer Team"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "michael@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert app_module.activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown%20Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email():
    response = client.post("/activities/Soccer%20Team/signup")

    assert response.status_code == 422


def test_remove_participant():
    email = "michael@mergington.edu"

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": "Removed michael@mergington.edu from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_remove_rejects_unknown_participant():
    response = client.delete(
        "/activities/Chess%20Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_remove_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown%20Club/signup", params={"email": "student@example.com"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_requires_email():
    response = client.delete("/activities/Chess%20Club/signup")

    assert response.status_code == 422


def test_static_index_is_served():
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "Mergington High School" in response.text