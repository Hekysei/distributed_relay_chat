from src.client.user_client import UserClient

if __name__ == "__main__":
    user = UserClient()
    user.send_user_text("c/client","/c")
