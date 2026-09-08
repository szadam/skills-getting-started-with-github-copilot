import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_activities = app_module.activities.copy()
    original_activity_data = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": list(details["participants"]),
        }
        for name, details in app_module.activities.items()
    }

    app_module.activities.clear()
    app_module.activities.update(original_activity_data)

    client = TestClient(app_module.app)
    yield client

    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert "participants" in response.json()[expected_activity]


def test_signup_adds_participant(client):
    # Arrange
    email = "newstudent@mergington.edu"
    app_module.activities["Chess Club"]["participants"] = ["michael@mergington.edu"]

    # Act
    response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities["Chess Club"]["participants"]
    assert response.json()["message"] == f"Signed up {email} for Chess Club"


def test_duplicate_signup_returns_400(client):
    # Arrange
    email = "michael@mergington.edu"
    app_module.activities["Chess Club"]["participants"] = [email]

    # Act
    response = client.post(f"/activities/Chess Club/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unknown_activity_returns_404(client):
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/Unknown Activity/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = "michael@mergington.edu"
    app_module.activities["Chess Club"]["participants"] = [email, "daniel@mergington.edu"]

    # Act
    response = client.delete(f"/activities/Chess Club/participants?email={email}")

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities["Chess Club"]["participants"]
    assert response.json()["message"] == f"Removed {email} from Chess Club"


def test_unregister_missing_participant_returns_404(client):
    # Arrange
    email = "notregistered@mergington.edu"
    app_module.activities["Chess Club"]["participants"] = ["michael@mergington.edu"]

    # Act
    response = client.delete(f"/activities/Chess Club/participants?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_full_activity_rejects_signup(client):
    # Arrange
    email = "newstudent@mergington.edu"
    app_module.activities["Chess Club"]["participants"] = [
        f"student{i}@mergington.edu" for i in range(12)
    ]
    app_module.activities["Chess Club"]["max_participants"] = 12

    # Act
    response = client.post(f"/activities/Chess Club/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
