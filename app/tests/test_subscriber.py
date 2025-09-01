from unittest import mock
from app.tests.base import BaseTest, new_async_client


class TestSubscriber(BaseTest):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.client = new_async_client()
        self.user = await self.setup_user()

    async def setup_user(self):
        """Helper function to create a user in the database."""
        create_user = {"email": "user@example.com", "password": "securepassword"}
        response = await self.client.post("/api/v1/users/", json=create_user)
        self.assertEqual(response.status_code, 200)
        user_data = response.json()
        expected_response = {
            "email": "user@example.com",
            "is_active": True,
            "is_superuser": False,
            "full_name": None,
            "id": mock.ANY,
        }
        self.assertEqual(user_data, expected_response)

        return user_data

    async def test_create_subscriber(self):
        """Test create subscriber through API."""
        # Build data for subscriber creation
        create_data = {
            "email": "fake@example.com",
            "first_name": "Fake",
            "last_name": "Subscriber",
            "tags": [],
            "custom_fields": {},
            "status": "active",
            "user_id": self.user["id"],
        }

        # Call the API to create a subscriber
        response = await self.client.post("/api/v1/subscribers", json=create_data)
        self.assertEqual(response.status_code, 201)
        subscriber_data = response.json()
        expected_date = {
            "email": "fake@example.com",
            "first_name": "Fake",
            "last_name": "Subscriber",
            "tags": [],
            "custom_fields": {},
            "status": "active",
            "id": mock.ANY,
            "user_id": self.user["id"],
            "source": "manual",
            "created_at": mock.ANY,
            "updated_at": None,
        }
        self.assertEqual(subscriber_data, expected_date)
