# Street Names Registration and Management System (SNRMS)

Ibeju-Lekki Local Government Area — Street naming lifecycle management platform.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, Tailwind CSS, HeadlessUI |
| Backend | Django 6, Django REST Framework, JWT (simplejwt) |
| Database | PostgreSQL 15 |
| Infrastructure | Docker Compose |

## Quick Start (Docker)

```bash
# Clone and enter the project
cd SNRMS

# Copy env file
cp backend/.env.example backend/.env

# Start all services
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DB_HOST=localhost and your PostgreSQL credentials

# Run migrations
python manage.py migrate

# Seed street types and default fees
python manage.py seed_data

# Create first Committee Chairman account
python manage.py create_chairman \
  --email chairman@ibeju-lekki.gov.ng \
  --password SecurePass123 \
  --first-name John \
  --last-name Doe

# Create Admin superuser (Django admin login uses email)
python manage.py shell -c "from accounts.models import User, Role; email='admin@ibeju-lekki.local'; u, _ = User.objects.get_or_create(email=email, defaults={'first_name':'Admin','last_name':'Admin','is_staff':True,'is_superuser':True,'role':Role.COMMITTEE_CHAIRMAN}); u.first_name='Admin'; u.last_name='Admin'; u.is_staff=True; u.is_superuser=True; u.role=Role.COMMITTEE_CHAIRMAN; u.set_password('ibeju-lekki'); u.save(); print('Admin superuser ready:', email)"

# Start development server
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## User Roles

| Role | Description |
|------|-------------|
| `applicant` | Self-registers; submits and tracks street naming applications |
| `finance` | Confirms/rejects payments; configures fee components; issues certificates |
| `naming_committee` | Reviews applications and recommends approval/rejection |
| `committee_chairman` | Final approval authority; manages staff accounts |

## Application Lifecycle

```
draft → submitted → awaiting_stage_a_payment → stage_a_confirmed
  → under_naming_committee_review → approved_by_committee
  → awaiting_chairman_approval → approved_by_chairman
  → awaiting_stage_c_payment → stage_c_confirmed
  → certificate_issued → [expired] → renewal flow → renewed
```

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/auth/register/ | Public self-registration (Applicant role) |
| POST | /api/auth/login/ | Login → JWT tokens |
| POST | /api/auth/token/refresh/ | Refresh access token |
| GET/PATCH | /api/auth/profile/ | Own profile |
| GET/POST | /api/applications/ | List / create applications |
| GET | /api/applications/:id/ | Application detail |
| POST | /api/applications/:id/submit/ | Submit draft application |
| POST | /api/applications/:id/withdraw/ | Withdraw application |
| POST | /api/applications/:id/committee-review/ | Committee approve/reject |
| POST | /api/applications/:id/chairman-approval/ | Chairman approve/reject |
| POST | /api/applications/:id/issue-certificate/ | Finance issues certificate |
| GET | /api/documents/?application=:id | List documents |
| POST | /api/documents/upload/ | Upload document |
| POST | /api/payments/:id/submit/ | Applicant submits payment reference |
| POST | /api/payments/:id/confirm/ | Finance confirms/rejects payment |
| GET | /api/payments/fees/breakdown/ | Fee breakdown for a stage |
| GET/PATCH | /api/payments/fees/config/:id/ | Finance updates fee amounts |
| GET | /api/config/street-types/ | List street types |
| GET | /api/notifications/ | Own notifications |

## Management Commands

```bash
# Bootstrap the first Chairman account
python manage.py create_chairman --email x@y.com --password P@ss1 --first-name A --last-name B

# Create Admin superuser (email login)
python manage.py shell -c "from accounts.models import User, Role; email='admin@ibeju-lekki.local'; u, _ = User.objects.get_or_create(email=email, defaults={'first_name':'Admin','last_name':'Admin','is_staff':True,'is_superuser':True,'role':Role.COMMITTEE_CHAIRMAN}); u.first_name='Admin'; u.last_name='Admin'; u.is_staff=True; u.is_superuser=True; u.role=Role.COMMITTEE_CHAIRMAN; u.set_password('ibeju-lekki'); u.save(); print('Admin superuser ready:', email)"

# Seed street types and default fee configurations
python manage.py seed_data

# Confirm email delivery is configured (sends one real message)
python manage.py send_test_email you@example.com
```

## Email

Registration codes, password resets and workflow notices are sent through
**SendGrid**, using its HTTPS API rather than SMTP — Fly.io restricts outbound
SMTP ports, and the API returns a usable error when a message is rejected.

| `SENDGRID_API_KEY` | `EMAIL_HOST` | Backend used |
| --- | --- | --- |
| set | — | SendGrid (production) |
| unset | set | plain SMTP (self-hosted fallback) |
| unset | unset | console — codes print to the server log |

Development needs no mail account: leave both unset and the verification code
appears in the runserver output.

To set it up in production:

1. SendGrid → **Settings → API Keys** → create a key with **Mail Send** access only.
2. SendGrid → **Settings → Sender Authentication** → verify the `DEFAULT_FROM_EMAIL`
   address, or authenticate the whole domain. SendGrid rejects mail from any
   unverified sender.
3. Set the secrets and confirm with `send_test_email`:

```bash
fly secrets set -a snrms-backend \
  SENDGRID_API_KEY='SG.xxxx' \
  DEFAULT_FROM_EMAIL='SNRMS Ibeju-Lekki <admin@snrms.com>'

fly ssh console -a snrms-backend -C 'python manage.py send_test_email you@example.com'
```

All sending goes through `notifications/mailer.py`; failures are logged rather
than raised, so a mail outage can never break a registration or an approval.

## Project Structure

```
SNRMS/
├── backend/
│   ├── accounts/       # Users, roles, JWT auth
│   ├── applications/   # Application lifecycle + state machine
│   ├── documents/      # File uploads
│   ├── payments/       # Payments, fee configuration
│   ├── notifications/  # In-app notifications
│   ├── audit/          # Activity logging
│   ├── config/         # Street types, fee setup
│   └── snrms/          # Django project settings + root URLs
├── frontend/
│   └── src/
│       ├── services/   # Axios API client
│       ├── stores/     # Pinia: auth, notifications
│       ├── router/     # Vue Router with role guards
│       ├── views/      # Pages (auth, applicant, staff, admin)
│       └── components/ # Shared UI components
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
└── docker-compose.yml
```
