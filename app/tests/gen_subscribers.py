import asyncio
import httpx
import uuid

# Define the endpoint URL
SUBSCRIBERS_URL = "http://localhost:8000/api/v1/subscribers"


# Function to generate subscriber data
def generate_subscribers(num_subscribers, user_id):
    subscribers = []
    for _ in range(num_subscribers):
        random_prefix = str(uuid.uuid4())[
            :8
        ]  # Generate a random UUID and take the first 8 characters
        subscriber = {
            "email": f"{random_prefix}@example.com",
            "first_name": f"User{random_prefix}",
            "last_name": "Name",
            "user_id": user_id,
        }
        subscribers.append(subscriber)
    return subscribers


# Function to create a single subscriber
async def create_subscriber(client, subscriber):
    try:
        response = await client.post(SUBSCRIBERS_URL, json=subscriber)
        if response.status_code == 201:
            print(f"Subscriber created: {subscriber['email']}")
        else:
            print(
                f"Failed to create subscriber: {subscriber['email']}, Status: {response.status_code}, Response: {response.text}"
            )
    except Exception as e:
        print(f"Error creating subscriber: {subscriber['email']}, Error: {e}")


# Function to create multiple subscribers concurrently
async def create_multiple_subscribers(subscribers):
    async with httpx.AsyncClient() as client:
        tasks = [create_subscriber(client, subscriber) for subscriber in subscribers]
        await asyncio.gather(*tasks)


# Run the script
if __name__ == "__main__":
    num_subscribers = 500
    user_id = "483c3ea2-5790-4d7f-a0fc-ee6b289cc0de"
    subscribers = generate_subscribers(num_subscribers, user_id)
    asyncio.run(create_multiple_subscribers(subscribers))
