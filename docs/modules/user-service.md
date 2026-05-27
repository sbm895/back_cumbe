# 🔹 Module Reference: User Service (`user-service`)

The **User Service** manages accounts, authentication, session tokens, user profiles, and push notification tokens. It runs internally on port `4001`.

---

## 📖 Explanation
The user service is the primary state management module for user records. It implements secure password hashing, issues JSON Web Tokens (JWT) for stateless sessions, and maps the `users` MongoDB collection using Beanie ODM. It also houses the `role` field used for publisher authorization, fields for tracking device tokens (`fcm_token`), and list arrays of events a user has favorited or attended.

---

## 📦 Libraries Utilized

*   `beanie` & `motor`: Asynchronous ODM and official MongoDB driver for document-schema mapping.
*   `bcrypt`: Secure cryptographic hashing for user passwords.
*   `PyJWT`: Encodes and decodes JSON Web Tokens (JWT) for stateless user sessions.
*   `fastapi`, `uvicorn`, `pydantic-settings`, `pydantic[email]`: Standard web and configuration parsing tools.

---

## 🛠️ How It Works

### 1. The Beanie MongoDB User Schema
The `User` model inherits from Beanie `Document`. All fields are fully annotated with custom validators such as `EmailStr` to prevent invalid records from reaching the database:

```python
class User(Document):
    name: str
    email: EmailStr
    role: Literal["user", "publisher"] = "user"
    hashed_password: Optional[str] = None
    fcm_token: Optional[str] = None            # Client device token
    profile_picture: Optional[str] = None      # Image url
    favorites: list[str] = []                  # Favorited event ID list
    attended_events: list[str] = []            # Attended event ID list

    class Settings:
        name = "users"                         # MongoDB collection name
```

### 2. Password Cryptographic Operations
Passwords are salted and hashed using `bcrypt` before storage. Verification checks the plain text against the database hash:

```python
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if hashed_password is None:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

### 3. Stateless Token Generation
Upon `/signup` or `/login`, the service generates a JWT using standard payload claims containing the user ID inside `sub` and the account role inside `role`. Signup and the generic create-user endpoint always default new accounts to `user`; publisher promotion is handled manually in MongoDB or controlled seed data:

```python
def create_access_token(user_id: str, role: str = "user") -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
```
Other services can resolve tokens by calling `verify_token(token)` or invoking the `/verify-token/{token}` HTTP route, which returns both `user_id` and `role`. Legacy tokens without `role` are treated as `user`.
