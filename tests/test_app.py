import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities_returns_activity_list(client):
    # Arrange
    expected_activity_name = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert expected_activity_name in activities
    assert activities[expected_activity_name]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Drama Workshop"
    email = "newstudent@mergington.edu"
    params = {"email": email}

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_for_activity_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    params = {"email": email}

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params=params)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert app_module.activities[activity_name]["participants"].count(email) == 1


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity_name = "Programming Class"
    email = "emma@mergington.edu"
    params = {"email": email}

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_remove_participant_returns_404_for_missing_student(client):
    # Arrange
    activity_name = "Gym Class"
    email = "absentstudent@mergington.edu"
    params = {"email": email}

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params=params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


@pytest.mark.parametrize(
    "method, path, payload, expected_detail",
    [
        ("post", "/activities/Unknown Club/signup", {"email": "test@mergington.edu"}, "Activity not found"),
        ("delete", "/activities/Unknown Club/participants", {"email": "test@mergington.edu"}, "Activity not found"),
    ],
)
def test_unknown_activity_returns_404(client, method, path, payload, expected_detail):
    # Arrange / Act
    response = getattr(client, method)(path, params=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail
