from itsdangerous import URLSafeSerializer

SECRET_KEY = "super-secret-key"
serializer = URLSafeSerializer(SECRET_KEY)

def create_session(username: str):
    return serializer.dumps({"user": username})

def verify_session(token: str):
    try:
        return serializer.loads(token)
    except:
        return None