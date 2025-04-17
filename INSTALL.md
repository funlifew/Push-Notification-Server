# Installation Guide

This guide will help you set up the Push Notification Server on your development machine.

## Prerequisites

- Python 3.12 or higher
- Poetry (dependency management)
- MySQL database
- Kavenegar API key (for SMS service)

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/push-notification-server.git
cd push-notification-server
```

## Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Generate VAPID keys for Web Push:
   ```bash
   # Install web-push if you don't have it
   npm install -g web-push
   
   # Generate keys
   web-push generate-vapid-keys
   
   # Or using OpenSSL
   openssl ecparam -name prime256v1 -genkey -noout -out private_key.pem
   openssl ec -in private_key.pem -pubout -out public_key.pem
   ```

3. Edit the `.env` file with your settings:
   - Set your database credentials
   - Add your Kavenegar API key
   - Add your VAPID keys
   - Set a strong JWT signing key

## Step 3: Install Dependencies

```bash
# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell
```

## Step 4: Initialize the Database

1. Create your MySQL database:
   ```sql
   CREATE DATABASE push_notification_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. Run migrations:
   ```bash
   python manage.py makemigrations accounts
   python manage.py makemigrations server
   python manage.py migrate
   ```

## Step 5: Create a Superuser

```bash
python manage.py createsuperuser
```

You'll be prompted to enter a phone number, email, first name, last name, and password.

## Step 6: Run the Development Server

```bash
python manage.py runserver
```

The development server will start at http://127.0.0.1:8000/

## Testing Web Push Notifications

1. Generate an admin token:
   ```bash
   curl -X POST http://localhost:8000/api/push/token/generate/
   ```

2. Use the token to send a test notification:
   ```bash
   curl -X POST http://localhost:8000/api/push/send/single/ \
     -H "Content-Type: application/json" \
     -d '{
       "admin_token": "your-admin-token",
       "subscription_info": {
         "endpoint": "https://fcm.googleapis.com/fcm/send/...",
         "keys": {
           "p256dh": "your-p256dh-key",
           "auth": "your-auth-key"
         }
       },
       "title": "Test Notification",
       "body": "This is a test notification!"
     }'
   ```

## Next Steps

- Review the API documentation in the README
- Set up a JavaScript client to subscribe to push notifications
- Configure your production environment with appropriate security settings

## Troubleshooting

- **Database Connection Issues**: Make sure your MySQL server is running and the credentials in `.env` are correct.
- **Migration Errors**: If you encounter migration errors, try deleting the migrations folder and recreating migrations.
- **SMS Sending Failures**: Verify your Kavenegar API key and ensure your account has sufficient credit.