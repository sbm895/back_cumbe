# 🔹 Module Reference: Payment Service (`payment-service`)

The **Payment Service** handles manual event ticket payments by generating unique, time-limited JWT tokens encoded as QR codes. It runs internally on port `4006`.

---

## 📖 Explanation
This service implements a manual confirmation workflow for paying event ticket entry:
1. When a user requests to buy an entry for a paid event (`/payments/initiate`), the service verifies the user and the event details by calling their respective microservices.
2. If verified, the service creates a payment record in MongoDB with the `PENDING` status.
3. The service then signs a JSON Web Token (JWT) with the user ID, event ID, and an expiration timestamp (e.g., 48 hours).
4. The JWT string is converted into a QR Code image (PNG formatted as a base64 string) and returned to the client.
5. In the background, the service calls the `notification-service` to email the QR code receipt to the user.
6. To confirm the purchase, the organizer scans the user's QR code, extracting the JWT token, and sends it to `/payments/validate`. The payment status updates to `COMPLETED`, triggering a successful entry notification to the user.

---

## 📦 Libraries Utilized

*   `beanie` & `motor`: Asynchronous ODM mapping the `payments` collection to MongoDB.
*   `PyJWT`: Signs and decodes the payment confirmation JWT tokens, and decodes session JWTs for publisher-only reports.
*   `qrcode`: Generates the visual QR codes representing the signed tokens.
*   `fastapi`, `uvicorn`, `pydantic-settings`: Web server and configuration parsers.
*   `httpx`: Async HTTP client to fetch details from `user-service`, `event-service`, and dispatch alerts through `notification-service`.

---

## 🛠️ How It Works

### 1. Payment Document Schema
The `Payment` model maintains references to the user and event, plus desnormalized metadata (`user_email`, `event_name`) for optimized reading:

```python
class PaymentStatus(str, Enum):
    PENDING    = "pending"     # Initiated, waiting manual confirmation
    COMPLETED  = "completed"   # Confirmed by scanning the QR code
    FAILED     = "failed"      # Cancelled or rejected

class Payment(Document):
    user_id: str
    event_id: str
    user_email: str
    event_name: str
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    qr_token: str
    qr_code_base64: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = None

    class Settings:
        name = "payments"
```

### 2. Publisher Authorization for Event Reports
The payment QR token is not a user session token and its payload remains `usuario_id`, `evento_id`, `tipo`, and `exp`. Publisher RBAC is applied only to `GET /payments/event/{event_id}`, which requires `Authorization: Bearer <session-token>` with `role: "publisher"`.

### 3. QR Token Generation
The service creates a JWT containing the transaction claims, then encodes it as a base64 PNG string:

```python
def generar_token_pago(usuario_id: str, evento_id: str) -> str:
    payload = {
        "usuario_id": usuario_id,
        "evento_id": evento_id,
        "tipo": "confirmacion_pago",
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def generar_qr_base64(token: str) -> str:
    qr = qrcode.make(token)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()
```

### 4. Verification and Confirmation
When the organizer scans the QR code, the token is verified and marked complete:

```python
@router.post("/validate")
async def validate_qr(body: ValidateQRRequest, background_tasks: BackgroundTasks):
    # Decode and validate JWT
    payload = validar_token_pago(body.token)
    usuario_id = payload.get("usuario_id")
    evento_id = payload.get("evento_id")

    # Fetch corresponding payment
    payment = await Payment.find_one(
        Payment.user_id == usuario_id,
        Payment.event_id == evento_id
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Payment already confirmed")

    # Finalize transaction
    payment.status = PaymentStatus.COMPLETED
    payment.confirmed_at = datetime.utcnow()
    await payment.save()

    # Dispatch FCM push and email alerts
    background_tasks.add_task(_notify_payment_confirmed, payment)
```
