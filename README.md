# Appointment Booking App

A lightweight appointment-booking demo for service-based bookings with a browser frontend, Python backend, and SQLite persistence.

## Overview

This project lets visitors:

- browse available services
- choose a date and time slot
- enter customer details and booking notes
- complete a payment flow (when Stripe is configured)
- receive a booking confirmation and calendar invite

The app stores booking data in SQLite and serves the frontend and API from a single Python HTTP server.

## Features

- Service catalog with pricing and duration
- Real-time slot availability checks
- Booking creation with validation
- Optional Stripe Checkout integration
- Booking confirmation page
- Calendar export (`.ics`) for confirmed appointments
- No external database required for local development

## Project Structure

- `index.html` — booking UI
- `script.js` — frontend logic and API calls
- `styles.css` — interface styling
- `server.py` — HTTP server and booking API
- `appointments.db` — SQLite database file
- `booking-confirmation.html` — confirmation page
- `.env.example` — sample environment variables
- `requirements.txt` — Python dependencies

## Tech Stack

- Python 3
- SQLite
- Vanilla HTML/CSS/JavaScript
- Optional Stripe integration

## Local Setup

1. Clone the repository.
2. Create and activate a virtual environment if desired.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (optional for Stripe):

   ```bash
   cp .env.example .env
   ```

   Then update the values in `.env` if you want payment processing enabled.

5. Start the application:

   ```bash
   python server.py
   ```

6. Open the app in a browser:

   ```text
   http://localhost:8000
   ```

## Environment Variables

The project supports these environment variables:

- `STRIPE_SECRET_KEY` — Stripe secret key for checkout flow
- `STRIPE_WEBHOOK_SECRET` — webhook signing secret
- `GOOGLE_CALENDAR_CREDENTIALS_JSON` — Google Calendar credentials for calendar integration
- `PUBLIC_BASE_URL` — base URL used for redirect links (defaults to `http://localhost:8000`)

If Stripe is not configured, the app falls back to a local confirmation page instead of a payment redirect.

## API Endpoints

- `GET /api/services` — returns all service offerings
- `GET /api/availability?date=YYYY-MM-DD&service_id=1` — returns available appointment slots
- `POST /api/bookings` — creates a booking
- `GET /api/bookings/<id>/calendar.ics` — downloads a calendar invite for a booking

## Notes

- The app initializes the SQLite database automatically on first run.
- Booking times are validated to prevent conflicts and ensure future appointment slots are used.
- The interface is intended as a demo and can be extended for production use with stronger validation, authentication, and payment processing.

## License

MIT.
