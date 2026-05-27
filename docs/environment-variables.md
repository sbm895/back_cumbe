# ⚙️ Environment Variables Reference

This reference details the complete list of environment variables used across the **back_cumbe** microservices ecosystem to configure database connections, credentials, networks, and integrations.

---

## 📋 Central Environmental Summary

These variables are defined in the central `.env` file at the root of the project and loaded by Docker Compose into the individual containers.

| Variable Name | Default Value | Target Services | Significance & Description |
| :--- | :--- | :--- | :--- |
| `MONGO_USER` | `admin` | `mongo`, `user-service`, `event-service`, `notification-service`, `payment-service`, `recommendation-service` | The root username for MongoDB authentication. |
| `MONGO_PASSWORD` | `secret` | `mongo`, `user-service`, `event-service`, `notification-service`, `payment-service`, `recommendation-service` | The root password for MongoDB authentication. |
| `MONGO_URL` | `mongodb://admin:secret@mongo:27017` | `user-service`, `event-service`, `notification-service`, `payment-service`, `recommendation-service` | Connection URI for the MongoDB instance. In Docker Compose, `mongo` resolves to the database container. |
| `MONGO_DB` | `users_db` | `user-service`, `event-service`, `notification-service`, `payment-service`, `recommendation-service` | Name of the shared database. All services share this database instance to coordinate data models. |
| `JWT_SECRET` | `your-super-secret-jwt-key-...` | `user-service`, `event-service`, `api-gateway` | Key used by `user-service` to sign JWT credentials and by protected services to verify session roles. *Change this in production!* |
| `JWT_ALGORITHM` | `HS256` | `user-service`, `event-service`, `payment-service` | Algorithm for token signatures. Defaults to HMAC-SHA256. |
| `USER_SERVICE_URL` | `http://user-service:4001` | `api-gateway`, `payment-service` | Network URL of the user microservice. Used by the gateway and payment service to proxy/resolve user endpoints. |
| `USUARIOS_URL` | `http://user-service:4001` | `notification-service` | Network URL of the user service container inside Docker Compose. |
| `EVENTOS_URL` | `http://event-service:4003` | `notification-service` | Network URL of the event service container inside Docker Compose. |
| `FIREBASE_CREDENTIALS_PATH` | `/app/firebase-credentials.json` | `notification-service` | Absolute path inside the container pointing to the Google Service Account key for Firebase. |
| `PAYMENT_SERVICE_URL` | `http://payment-service:4006` | `api-gateway` | Network URL of the payment microservice. Used by the gateway to proxy payment endpoints. |
| `RECOMMATION_SERVICE_URL` | `http://recommendation-service:4005` | `api-gateway` | Network URL of the recommendation microservice. |
| `EVENT_SERVICE_URL` | `http://event-service:4003` | `payment-service`, `recommendation-service` | Network URL of the event microservice. |
| `NOTIFICATION_SERVICE_URL` | `http://notification-service:4004` | `payment-service` | Network URL of the notification microservice. |
| `JWT_SECRET_KEY` | `your-secret-key-change-in-env` | `payment-service` | Secret key used to sign and verify manual QR-code payment verification tokens. |

---

## 🛠️ Service Specific Load Out

### 1. `api-gateway`
Defined in `services/api-gateway/src/config.py`:
*   `user_service_url`: Loaded from `USER_SERVICE_URL` (default: `http://user-service:4001`). Used as the host destination for proxying requests.

### 2. `user-service`
Defined in `services/user-service/src/config.py`:
*   `mongo_url`: Loaded from `MONGO_URL`. (Required)
*   `mongo_db`: Loaded from `MONGO_DB` (default: `users_db`).
*   `jwt_secret`: Loaded from `JWT_SECRET`. (Required)
*   `jwt_algorithm`: Loaded from `JWT_ALGORITHM` (default: `HS256`).

### 3. `event-service`
Defined in `services/event-service/src/config.py`:
*   `mongo_url`: Loaded from `MONGO_URL`. (Required)
*   `mongo_db`: Loaded from `MONGO_DB` (default: `users_db`).
*   `jwt_secret`: Loaded from `JWT_SECRET`. Used to verify publisher session tokens. (Required)
*   `jwt_algorithm`: Loaded from `JWT_ALGORITHM` (default: `HS256`).

### 4. `notification-service`
Defined in `services/notification-service/src/config.py`:
*   `mongo_url`: Loaded from `MONGO_URL`. (Required)
*   `mongo_db`: Loaded from `MONGO_DB` (default: `users_db`).
*   `firebase_credentials_path`: Loaded from `FIREBASE_CREDENTIALS_PATH` (default: `firebase-credentials.json`).
*   `eventos_url`: Loaded from `EVENTOS_URL` (default: `http://eventos-service:4003`). *Note: Configured in code as `http://eventos-service:4003` but in docker-compose overridden as `http://event-service:4003`.*
*   `usuarios_url`: Loaded from `USUARIOS_URL` (default: `http://user-service:4001`).

### 5. `payment-service`
Defined in `services/payment-service/src/config.py`:
*   `mongo_url`: Loaded from `MONGO_URL`. (Required)
*   `mongo_db`: Loaded from `MONGO_DB` (default: `users_db`).
*   `user_service_url`: Loaded from `USER_SERVICE_URL` (default: `https://back-cumbe-users.onrender.com`).
*   `event_service_url`: Loaded from `EVENT_SERVICE_URL` (default: `https://back-cumbe-events.onrender.com`).
*   `notification_service_url`: Loaded from `NOTIFICATION_SERVICE_URL` (default: `https://back-cumbe-notifs.onrender.com`).
*   `jwt_secret_key`: Loaded from `JWT_SECRET_KEY` (default: `your-secret-key-change-in-env`). In Docker Compose this is mapped from `JWT_SECRET`, so the service can validate publisher session tokens for event payment reports.
*   `jwt_algorithm`: Loaded from `JWT_ALGORITHM` (default: `HS256`).
*   `jwt_expiration_hours`: Loaded from `JWT_EXPIRATION_HOURS` (default: `48`).

### 6. `recommendation-service`
Defined in `services/recommendation-service/src/config.py`:
*   `mongo_url`: Loaded from `MONGO_URL`. (Required)
*   `mongo_db`: Loaded from `MONGO_DB` (default: `users_db`).
*   `EVENT_SERVICE_URL`: Loaded from `EVENT_SERVICE_URL` (default: `https://back-cumbe-events.onrender.com/events/`).
