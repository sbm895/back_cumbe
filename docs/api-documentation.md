# 🔌 Complete API Reference Manual

This reference catalog documents all endpoints, request schemas, and expected responses for the **back_cumbe** microservice ecosystem.

---

## 🔀 1. API Gateway (`api-gateway`)
*Port: `3000`*

The Gateway exposes routes and proxies them to downstream microservices. Currently, user, event, and notification routes are mapped.

### Session JWT and RBAC
Session tokens are issued by `/users/signup` and `/users/login`. Their payload contains:
```json
{
  "sub": "MongoDB-User-Object-ID",
  "role": "user",
  "iat": 1716700000
}
```
Valid roles are `user` and `publisher`. Existing tokens without `role` are treated as `user`. Endpoints marked as publisher-only require `Authorization: Bearer <token>` with `role: "publisher"`.

### Health Check
*   **Method:** `GET`
*   **Path:** `/health`
*   **Description:** Returns Gateway operational status.
*   **Response:**
    ```json
    {"status": "ok", "service": "api-gateway"}
    ```

### User Endpoints Proxy
*   **Method:** `GET`, `POST`, `PUT`, `DELETE`
*   **Path:** `/users/{path:path}`
*   **Description:** Proxies any request starting with `/users/...` directly to the `user-service`.

### Event Endpoints Proxy
*   **Method:** `GET`, `POST`, `PUT`, `DELETE`
*   **Path:** `/events/{path:path}`
*   **Description:** Proxies any request starting with `/events/...` directly to the `event-service`.

### Notification Endpoints Proxy
*   **Method:** `GET`, `POST`, `PUT`, `DELETE`
*   **Path:** `/notifications/{path:path}`
*   **Description:** Proxies any request starting with `/notifications/...` directly to the `notification-service`.

### Payment Endpoints Proxy
*   **Method:** `GET`, `POST`, `PUT`, `DELETE`
*   **Path:** `/payments/{path:path}`
*   **Description:** Proxies any request starting with `/payments/...` directly to the `payment-service`.

---

## 👤 2. User Service (`user-service`)
*Port: `4001`*

Handles registration, session creation, profile editing, and device FCM tokens.

### User Signup
*   **Method:** `POST`
*   **Path:** `/users/signup`
*   **Description:** Creates a standard user account with `role: "user"`. Publisher promotion is handled manually in MongoDB or controlled seed data.
*   **Request Body (JSON):**
    ```json
    {
      "name": "string",
      "email": "user@example.com",
      "password": "password123"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "access_token": "JWT-Token-String",
      "token_type": "bearer"
    }
    ```

### User Login
*   **Method:** `POST`
*   **Path:** `/users/login`
*   **Request Body (JSON):**
    ```json
    {
      "email": "user@example.com",
      "password": "password123"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "access_token": "JWT-Token-String",
      "token_type": "bearer"
    }
    ```

### Token Verification
*   **Method:** `GET`
*   **Path:** `/users/verify-token/{token}`
*   **Description:** Used by other microservices to decode and validate JWTs.
*   **Response (200 OK):**
    ```json
    {
      "user_id": "MongoDB-Object-ID",
      "role": "user"
    }
    ```

### List All Users
*   **Method:** `GET`
*   **Path:** `/users/`
*   **Response (200 OK):** Array of User objects.

### Fetch Users in Batch
*   **Method:** `POST`
*   **Path:** `/users/batch`
*   **Request Body (JSON):**
    ```json
    {
      "ids": ["User-ID-1", "User-ID-2"]
    }
    ```
*   **Response (200 OK):** Array of matching User objects.

### Fetch Single User
*   **Method:** `GET`
*   **Path:** `/users/{user_id}`
*   **Response (200 OK):**
    ```json
    {
      "_id": "MongoDB-Object-ID",
      "name": "Juan Perez",
      "email": "juan.perez@example.com",
      "role": "user",
      "fcm_token": "fcm-token-string-or-null",
      "profile_picture": "string-or-null",
      "favorites": [],
      "attended_events": []
    }
    ```

### Update User Profile
*   **Method:** `PUT`
*   **Path:** `/users/{user_id}`
*   **Request Body (JSON):** Complete User JSON.
*   **Description:** Updates editable profile fields only; `role` is not changed by this endpoint.
*   **Response (200 OK):** Updated User object.

### Update FCM Token
*   **Method:** `PUT`
*   **Path:** `/users/{user_id}/fcm_token`
*   **Params:** `fcm_token: str` (Query param)
*   **Response (200 OK):**
    ```json
    {"message": "FCM token updated successfully"}
    ```

### Get FCM Token
*   **Method:** `GET`
*   **Path:** `/users/{user_id}/fcm_token`
*   **Response (200 OK):**
    ```json
    {"fcm_token": "fcm-token-string-or-null"}
    ```

### Delete User
*   **Method:** `DELETE`
*   **Path:** `/users/{user_id}`
*   **Response (200 OK):**
    ```json
    {"message": "User deleted successfully"}
    ```

---

## 📅 3. Event Service (`event-service`)
*Port: `4003`*

Manages event creation, categories, user attendance, and organizers.

### Create Event (Independent)
*   **Method:** `POST`
*   **Path:** `/events/`
*   **Authorization:** Publisher-only Bearer token.
*   **Request Body (JSON):** Complete Event Document schema.
*   **Response (201 Created):** Created Event object.

### Create Event for User (Organized)
*   **Method:** `POST`
*   **Path:** `/events/{user_id}/events`
*   **Authorization:** Publisher-only Bearer token.
*   **Description:** Assigns the user as the `organizer` and registers the event.
*   **Response (200 OK):** Created Event object.

### Get Event
*   **Method:** `GET`
*   **Path:** `/events/{event_id}`
*   **Response (200 OK):**
    ```json
    {
      "_id": "Event-Object-ID",
      "name": "Carnaval Picó Fest",
      "description": "Verbena popular de picó",
      "date": "2026-05-19T20:00:00",
      "picture": ["path-to-image"],
      "location": "Barrio Abajo, Barranquilla",
      "organizer": { ...User Object... },
      "attendees": ["User-ID-1", "User-ID-2"],
      "categories": ["champeta", "picó"]
    }
    ```

### Update Event
*   **Method:** `PUT`
*   **Path:** `/events/{event_id}`
*   **Authorization:** Publisher-only Bearer token.
*   **Request Body (JSON):** Update fields.
*   **Response (200 OK):** Updated Event object.

### Delete Event
*   **Method:** `DELETE`
*   **Path:** `/events/{event_id}`
*   **Authorization:** Publisher-only Bearer token.
*   **Response (200 OK):**
    ```json
    {"message": "Event deleted successfully"}
    ```

### Register Attendance
*   **Method:** `POST`
*   **Path:** `/events/{event_id}/attend`
*   **Params:** `user_id: str` (Query param)
*   **Description:** Appends the user ID to the event's attendee list, and the event ID to the user's attended list.
*   **Response (200 OK):**
    ```json
    {"message": "User is now attending the event"}
    ```

### Cancel Attendance
*   **Method:** `DELETE`
*   **Path:** `/events/{event_id}/attend`
*   **Params:** `user_id: str` (Query param)
*   **Response (200 OK):**
    ```json
    {"message": "User is no longer attending the event"}
    ```

### Get Event Attendees
*   **Method:** `GET`
*   **Path:** `/events/{event_id}/attendees`
*   **Response (200 OK):**
    ```json
    ["User-ID-1", "User-ID-2"]
    ```

### List Events by Category
*   **Method:** `GET`
*   **Path:** `/events/category/{category_name}`
*   **Response (200 OK):** Array of Event objects matching the category filter.

### List Popular Events
*   **Method:** `GET`
*   **Path:** `/events/popular`
*   **Description:** Lists popular events based on attendance.

### List Incoming Events
*   **Method:** `GET`
*   **Path:** `/events/incoming`
*   **Description:** Lists all incoming upcoming events.

### Upload Event Image
*   **Method:** `POST`
*   **Path:** `/events/{event_id}/upload-image`
*   **Authorization:** Publisher-only Bearer token.
*   **Request Body:** `multipart/form-data` with `file`.
*   **Response (200 OK):** Cloudinary URL and event ID.

### Delete Event Image
*   **Method:** `DELETE`
*   **Path:** `/events/{event_id}/images`
*   **Authorization:** Publisher-only Bearer token.
*   **Params:** `image_url: str` (Query param)
*   **Response (200 OK):**
    ```json
    {"message": "Image deleted", "event_id": "Event-ID", "url": "https://..."}
    ```

---

## 🔔 4. Notification Service (`notification-service`)
*Port: `4004`*

Manages background push triggers and scheduled event notifications.

### Send Direct Push Notification
*   **Method:** `POST`
*   **Path:** `/send-direct` (Proxied as `/notifications/send-direct`)
*   **Request Body (JSON):**
    ```json
    {
      "token": "fcm-device-token",
      "title": "Notification Title",
      "body": "Notification Body",
      "data": {}
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Notification dispatched"
    }
    ```

---

## 💳 5. Payment Service (`payment-service`)
*Port: `4006` (Proxied via API Gateway under `/payments`)*

Handles manual payment initialization, QR code/JWT generation, and QR code verification.

### Initiate Payment (and Generate QR)
*   **Method:** `POST`
*   **Path:** `/payments/initiate`
*   **Request Body (JSON):**
    ```json
    {
      "user_id": "MongoDB-User-Object-ID",
      "event_id": "MongoDB-Event-Object-ID"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "payment_id": "MongoDB-Payment-Object-ID",
      "amount": 25000.0,
      "event_name": "Carnaval Picó Fest",
      "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "qr_token": "eyJhbGciOiJIUzI1Ni...",
      "status": "pending"
    }
    ```

### Validate QR Code (Confirm Payment)
*   **Method:** `POST`
*   **Path:** `/payments/validate`
*   **Request Body (JSON):**
    ```json
    {
      "token": "eyJhbGciOiJIUzI1Ni..."
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "message": "Pago confirmado exitosamente",
      "event_id": "MongoDB-Event-Object-ID",
      "user_id": "MongoDB-User-Object-ID",
      "payment_id": "MongoDB-Payment-Object-ID"
    }
    ```

### Fetch Single Payment
*   **Method:** `GET`
*   **Path:** `/payments/{payment_id}`
*   **Response (200 OK):**
    ```json
    {
      "id": "MongoDB-Payment-Object-ID",
      "user_id": "MongoDB-User-Object-ID",
      "event_id": "MongoDB-Event-Object-ID",
      "user_email": "user@example.com",
      "event_name": "Carnaval Picó Fest",
      "amount": 25000.0,
      "status": "pending",
      "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "created_at": "2026-05-26T08:00:00Z",
      "updated_at": "2026-05-26T08:00:00Z",
      "confirmed_at": null
    }
    ```

### Fetch User Payments History
*   **Method:** `GET`
*   **Path:** `/payments/user/{user_id}`
*   **Response (200 OK):** Array of Payment objects, sorted by creation date descending.

### Fetch Event Payments History
*   **Method:** `GET`
*   **Path:** `/payments/event/{event_id}`
*   **Authorization:** Publisher-only Bearer token.
*   **Response (200 OK):** Array of Payment objects associated with the event.

### Cancel Payment
*   **Method:** `POST`
*   **Path:** `/payments/{payment_id}/cancel`
*   **Response (200 OK):** Updated Payment object with status set to `failed`.

---

## 🧠 6. Recommendation Service (`recommendation-service`)
*Port: `4005` (Direct internal access only)*

Handles the generation of custom hybrid event recommendations for users.

### Get User Recommendations
*   **Method:** `GET`
*   **Path:** `/recs/{user_id}`
*   **Params:** `limit: int` (Query param, default: 10)
*   **Response (200 OK):** Ordered array of recommended Event objects (combining content similarity, friends boost, and collaborative cosine similarity).

### Health Check
*   **Method:** `GET`
*   **Path:** `/health`
*   **Response (200 OK):**
    ```json
    {"status": "ok", "service": "recommendation-service"}
    ```
