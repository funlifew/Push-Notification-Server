# 🔔 Push Notification Server

A comprehensive Django-based server for managing users and sending web push notifications.

```
 ______   _     _   ______   _    _
|  __  | | |   | | |  ____| | |  | |
| |__| | | |   | | | |____  | |__| |
|  ____| | |   | | |____  | |  __  |
| |      | |___| | _____| | | |  | |
|_|      |_______||______| |_|  |_|
```

## 🌟 Features

- **User Authentication System**
  - Phone number-based authentication with OTP verification
  - JWT token authentication with secure HttpOnly cookies
  - Password reset functionality
  - Profile management

- **Push Notification Service**
  - Send notifications to individual subscribers
  - Send batch notifications to groups
  - Token-based administration

## 🛠 Technology Stack

- **Backend**: Django, Django REST Framework
- **Authentication**: JWT (JSON Web Tokens)
- **Database**: MySQL
- **Push Notifications**: Web Push API with Vapid keys
- **SMS Integration**: Kavenegar API for OTP delivery

## 📋 Prerequisites

- Python 3.12+
- Poetry for dependency management
- MySQL database
- Kavenegar API key (for SMS delivery)
- Vapid keys for Web Push

## ⚙️ Environment Setup

1. Clone the repository
2. Create a `.env` file based on the `.env.example` template
3. Generate Vapid keys:
   ```bash
   openssl ecparam -name prime256v1 -genkey -noout -out private_key.pem
   openssl ec -in private_key.pem -pubout -out public_key.pem
   ```
4. Configure your database settings in the `.env` file
5. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

## 🚀 Getting Started

1. Apply migrations:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Access the admin interface at `http://localhost:8000/admin/`

## 📝 API Documentation

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register/` | POST | Register a new user |
| `/api/auth/login/` | POST | Log in and get tokens |
| `/api/auth/logout/` | POST | Log out and invalidate tokens |
| `/api/auth/token/refresh/` | POST | Refresh access token |
| `/api/auth/otp/verify/` | POST | Verify OTP code |
| `/api/auth/password/change/` | POST | Change user password |
| `/api/auth/password/reset/request/` | POST | Request password reset |
| `/api/auth/password/reset/` | POST | Reset password with OTP |
| `/api/auth/profile/` | GET/POST | Get or update profile |
| `/api/auth/number/change/` | POST | Change phone number |

### Push Notification Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/push/token/generate/` | POST | Generate admin token |
| `/api/push/send/single/` | POST | Send notification to a single device |
| `/api/push/send/group/` | POST | Send notification to multiple devices |

## 🛡️ Security Best Practices

- JWT tokens are stored in HttpOnly cookies for XSS protection
- Phone numbers are validated and normalized using the `phonenumbers` library
- OTP codes expire after 5 minutes and can only be refreshed after 2 minutes
- Admin tokens are required for sending notifications

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PyWebPush](https://github.com/web-push-libs/pywebpush)
- [Kavenegar](https://kavenegar.com/) for SMS services

---

Made with ❤️ by Mehdi Radfar