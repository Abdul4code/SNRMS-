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

### Who holds a street

One street, one applicant — but only while that applicant keeps moving. Two
selections within 75 m count as the same street.

| Applicant's position | Street is held | Then |
| --- | --- | --- |
| Applied, fee not paid | 3 days from applying | Opens to everyone again |
| Fee paid, decision pending | 1 month from the payment | Opens to everyone again |
| Name granted (Chairman approved onward) | Permanently | Never reopens |

The applicant is shown the countdown on their application, and is told plainly
that the street opens up if they do not pay in time. Rejecting or withdrawing an
application releases the street immediately.

A street that reopens can collect several applications. **None is rejected
automatically** — staff see "2nd of 3 applications for this same location" on the
application, with links to the others and which one still holds the street, and
the council chooses.

Holds are derived from the application's status and its payment timestamps
(`applications/street_locks.py`), never stored, so they cannot drift out of step
with the application and expiry needs no scheduled job.

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

# --- Fees (see "Fees" below) ---
python manage.py sync_fee_schedule                # recompute revalidation/renewal
python manage.py sync_fee_schedule --apply-base   # also apply the official base schedule
python manage.py demo_fees                        # shrink every fee for gateway testing
python manage.py reset_fees                       # restore the official schedule

# --- Going live (see "Testing and Go-Live" below) ---
python manage.py go_live                          # report only — changes nothing
python manage.py go_live --yes                    # migrate, clear test data, apply real fees
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

## Fees

Registration is charged in two stages (A and C). Two further fees are a
**percentage of the street type's Stage C street-name fee**, held in the
`FeePolicy` singleton:

| Fee | Share | When it is charged |
| --- | --- | --- |
| Revalidation | **40%** | An already-named street is brought onto the digital register (a legacy application). Charged instead of Stage C. |
| Renewal | **5%** | An existing registration is renewed before or after expiry. |

Official base schedule:

| Street type | Base | Revalidation | Renewal |
| --- | ---: | ---: | ---: |
| Avenue | ₦2,000,000 | ₦800,000 | ₦100,000 |
| Crescent | ₦1,500,000 | ₦600,000 | ₦75,000 |
| Way | ₦1,000,000 | ₦400,000 | ₦50,000 |
| Street / Lane / Close | ₦500,000 | ₦200,000 | ₦25,000 |

Street types not on the LGA sheet (Road, Drive, Boulevard, Court and the
specialised types) keep their own base fee and derive by the same percentages.

The percentages are the source of truth, but the derived amounts are stored as
ordinary `FeeConfiguration` rows so Finance can override a single street type in
the admin UI. `sync_fee_schedule` rewrites them from the policy; amounts round
to whole naira, because a kobo remainder stops an applicant's transfer ever
matching `amount_expected` exactly.

```bash
# Preview before changing anything
python manage.py sync_fee_schedule --apply-base --dry-run
```

Changing a base fee or a percentage takes effect on the next `sync_fee_schedule`
run, which also re-prices any payment still pending.

## Testing and Go-Live

### Testing mode

Real fees are far above what a payment gateway will accept for a test
transaction, so shrink them first. `demo_fees` keeps every *payable stage* above
the gateway minimum (default ₦100) while making each fee small:

```bash
python manage.py demo_fees            # or: --min 50
```

Testers can then register, pay, and run applications through the full lifecycle
for a few naira. Restore the official schedule at any time:

```bash
python manage.py reset_fees
```

Both commands re-price payments that are still pending, so applications created
mid-test keep matching the schedule in force.

### Going live

One command. It migrates, clears the test data, applies the official fee
schedule and verifies the result:

```bash
# 1. Ship the code
fly deploy -a snrms-backend

# 2. Back up — this is not reversible
# (backups must be enabled once: fly postgres backup enable -a snrms-db)
fly postgres backup create -a snrms-db

# 3. Report only: shows what would be deleted and previews the fee table
fly ssh console -a snrms-backend -C 'python manage.py go_live'

# 4. Do it
fly ssh console -a snrms-backend -C 'python manage.py go_live --yes'
```

**Most of the production database is not test data.** The digitised old registry
is stored as legacy applications owned by `legacy-registry@ibeju-lekki.gov.ng`,
and the street registry links to them. A blanket wipe would destroy imported
council records, so the reset is deliberately scoped:

| Kept | Removed |
| --- | --- |
| **Every staff account** — finance, naming committee, chairman, superusers | Public applicant accounts |
| The legacy import account and the digitised old registry | Non-legacy (test) applications |
| Street registry and building survey | Their payments, receipts, documents, status history, committee reviews, notifications |
| Street types, fee configuration, fee policy, renewal settings | Outstanding email verification codes |
| The Treasurer's signature | Uploaded files belonging to deleted records |

**No staff account is ever deleted.** There is no flag to do it — the council's
back office has to work the moment the system opens. Applicant accounts that
will be removed are listed by name in the report before anything happens.

After the reset, `go_live` asserts the end state: no test applications or
payments left, a superuser still present, no staff account missing, the street
registry and building survey intact, and a revalidation fee configured for every
street type. It reports `PROBLEM:` lines and a non-clean summary if any of that
fails.

Re-running `go_live --yes` is safe.

**Applicants holding a legacy import.** `Application.applicant` is `PROTECT`ed,
so an applicant account that owns a record in the old registry is kept rather
than deleted. If such an account really should go, add `--reassign-legacy`: the
import moves to `legacy-registry@ibeju-lekki.gov.ng` (the record survives, only
its nominal owner changes) and the account is then removed.

```bash
fly ssh console -a snrms-backend -C 'python manage.py go_live --yes --reassign-legacy'
```

Other flags: `--keep-media` leaves uploaded files on disk. The underlying
`reset_for_golive` command can be run on its own if you want the cleanup without
the fee change, and carries a `--purge-legacy` flag that deletes the old
registry — only ever appropriate on a database with no real imports.

**Reference numbers continue, they do not restart.** Numbering counts every
application created in the current year and the legacy imports are real records,
so the next application follows on from them rather than returning to `00001`.
Restarting would collide with reference numbers already issued.

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
