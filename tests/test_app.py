"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Arrange-Act-Assert: Verify all activities are returned"""
        # Arrange: client is ready
        # Act: Make request to get activities
        response = client.get("/activities")
        
        # Assert: Check response
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 4
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        assert "Art Club" in activities
    
    def test_get_activities_returns_activity_details(self, client):
        """Arrange-Act-Assert: Verify activity details are included"""
        # Arrange: client is ready
        # Act: Make request to get activities
        response = client.get("/activities")
        activities = response.json()
        
        # Assert: Check activity structure
        chess_club = activities["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert isinstance(chess_club["participants"], list)
        assert len(chess_club["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_success(self, client):
        """Arrange-Act-Assert: Successfully sign up a new participant"""
        # Arrange: New student email
        student_email = "alice@mergington.edu"
        activity_name = "Chess Club"
        
        # Act: Sign up for activity
        response = client.post(
            f"/activities/{activity_name}/signup?email={student_email}",
            params={"email": student_email}
        )
        
        # Assert: Check success response
        assert response.status_code == 200
        assert student_email in response.json()["message"]
    
    def test_signup_increases_participant_count(self, client):
        """Arrange-Act-Assert: Verify participant count increases after signup"""
        # Arrange: Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Art Club"]["participants"])
        
        # Act: Sign up new participant to activity with no participants
        student_email = "newstudent@mergington.edu"
        client.post(
            f"/activities/Art Club/signup?email={student_email}",
            params={"email": student_email}
        )
        
        # Assert: Verify participant was added
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Art Club"]["participants"])
        assert final_count == initial_count + 1
        assert student_email in final_response.json()["Art Club"]["participants"]
    
    def test_signup_duplicate_student_returns_400(self, client):
        """Arrange-Act-Assert: Prevent duplicate signup"""
        # Arrange: Student already signed up to Chess Club
        existing_student = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act: Try to sign up same student again
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_student}",
            params={"email": existing_student}
        )
        
        # Assert: Verify error response
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Arrange-Act-Assert: Handle signup to non-existent activity"""
        # Arrange: Non-existent activity
        activity_name = "Non-Existent Club"
        student_email = "student@mergington.edu"
        
        # Act: Try to sign up to non-existent activity
        response = client.post(
            f"/activities/{activity_name}/signup?email={student_email}",
            params={"email": student_email}
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_existing_participant_success(self, client):
        """Arrange-Act-Assert: Successfully remove an existing participant"""
        # Arrange: Participant in Chess Club
        activity_name = "Chess Club"
        participant_email = "michael@mergington.edu"
        
        # Act: Remove participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{participant_email}"
        )
        
        # Assert: Check success response
        assert response.status_code == 200
        assert participant_email in response.json()["message"]
    
    def test_remove_decreases_participant_count(self, client):
        """Arrange-Act-Assert: Verify participant count decreases after removal"""
        # Arrange: Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        participant_to_remove = "michael@mergington.edu"
        
        # Act: Remove participant
        client.delete(
            f"/activities/Chess Club/participants/{participant_to_remove}"
        )
        
        # Assert: Verify participant was removed
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Chess Club"]["participants"])
        assert final_count == initial_count - 1
        assert participant_to_remove not in final_response.json()["Chess Club"]["participants"]
    
    def test_remove_nonexistent_participant_returns_404(self, client):
        """Arrange-Act-Assert: Handle removal of non-existent participant"""
        # Arrange: Non-existent participant
        activity_name = "Chess Club"
        nonexistent_email = "nonexistent@mergington.edu"
        
        # Act: Try to remove non-existent participant
        response = client.delete(
            f"/activities/{activity_name}/participants/{nonexistent_email}"
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """Arrange-Act-Assert: Handle removal from non-existent activity"""
        # Arrange: Non-existent activity
        nonexistent_activity = "Non-Existent Club"
        email = "student@mergington.edu"
        
        # Act: Try to remove from non-existent activity
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants/{email}"
        )
        
        # Assert: Verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_remove_workflow(self, client):
        """Arrange-Act-Assert: Complete signup and removal workflow"""
        # Arrange: New student
        student_email = "testuser@mergington.edu"
        activity_name = "Art Club"
        
        # Act & Assert: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={student_email}",
            params={"email": student_email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        check_response = client.get("/activities")
        assert student_email in check_response.json()[activity_name]["participants"]
        
        # Act: Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/participants/{student_email}"
        )
        
        # Assert: Verify removal
        assert remove_response.status_code == 200
        final_response = client.get("/activities")
        assert student_email not in final_response.json()[activity_name]["participants"]
