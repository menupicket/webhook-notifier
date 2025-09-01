from unittest import mock
from app.tests.base import BaseTest, new_async_client


class TestUser(BaseTest):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.client = new_async_client()

    async def test_create_user(self):
        """Test create user through API."""
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
