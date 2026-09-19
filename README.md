Event & Conference Management System

Project Overview

The Event & Conference Management System is a FastAPI-based backend application designed to manage events, conferences, organizers, attendees, speakers, venues, sessions, registrations, tickets, payments, notifications, check-ins, certificates, feedback, and audit logs.

The system provides role-based access control and RESTful APIs for managing the complete event lifecycle, from event creation and attendee registration to payment, session management, check-in, certificate generation, feedback, and auditing.

Technology Stack

* Python 3.10+
* FastAPI
* SQLAlchemy
* Pydantic
* Pydantic Settings
* SQLite
* Alembic
* JWT Authentication
* Passlib / Password Hashing
* Pytest
* Uvicorn

User Roles

The system supports the following roles:

1. Admin

   * Manage the overall system
   * Manage events
   * Manage venues
   * Manage users and system-level operations
   * Access administrative functionality

2. Event Organizer

   * Create and manage events
   * Manage event-related information
   * Manage speakers, sessions, and event activities

3. Speaker

   * Manage speaker information
   * Participate in event sessions
   * Receive attendee feedback

4. Staff

   * Support event operations
   * Manage operational activities such as check-in

5. Attendee

   * Register for events
   * Purchase tickets
   * Make payments
   * Attend sessions
   * Check in to events
   * Submit feedback
   * Receive certificates and notifications

Main Features

Authentication and Authorization

* User registration
* User login
* JWT access tokens
* JWT refresh tokens
* Current-user information
* Password hashing
* Role-based authorization
* Active/inactive user validation
* Refresh token management and revocation

Event Management

* Create events
* View events
* View individual event details
* Update events
* Delete events
* Event type management
* Event status management
* Organizer validation
* Event capacity management
* Registration date validation
* Event date validation
* Event filtering
* Event sorting
* Pagination
* Available-capacity filtering

Supported Event Types

* Conference
* Workshop
* Seminar
* Meetup
* Training

Event Statuses

* Draft
* Published
* Registration Open
* Registration Closed
* Completed
* Cancelled

Venue and Hall Management

* Create venues
* View venue details
* Update venues
* Delete venues
* Venue capacity management
* Venue status management
* Hall management
* Hall availability management
* Venue and hall validation

Speaker Management

* Create speaker profiles
* View speakers
* Update speaker information
* Delete speakers
* Speaker expertise
* Speaker company information
* Speaker experience
* Speaker activation status
* Speaker-session assignment

Attendee Management

* Create attendee profiles
* View attendee profiles
* View own attendee profile
* Update own attendee profile
* Retrieve attendee information
* Duplicate profile prevention
* Role-based attendee access

Event Registration

* Register attendees for events
* Validate event availability
* Validate event capacity
* Registration status management
* Registration cancellation
* Registration validation
* Prevent registration for invalid or cancelled events
* Attendee-specific registration access

Ticket Management

* Create tickets
* Manage ticket types
* Ticket pricing
* Ticket quantity management
* Ticket sale start and end dates
* Ticket availability validation
* Ticket activation/deactivation
* Ticket purchase validation

Ticket Purchases

* Purchase tickets
* Validate ticket availability
* Calculate purchase amounts
* Manage purchased tickets
* Prevent invalid purchases
* Track ticket purchase information

Payment Management

* Create payments
* Track payment status
* Validate payment amounts
* Payment-related event and ticket validation
* Payment status handling
* Refund-related functionality

Notification Management

* Create notifications
* Retrieve notifications
* Mark notifications as read
* User-specific notifications
* Event-related notifications
* Notification status management

Session Management

* Create event sessions
* Update sessions
* Delete sessions
* Session scheduling
* Speaker assignment
* Session capacity
* Session booking
* Session validation
* Prevent invalid session bookings

Check-in Management

* Attendee check-in
* Registration validation
* Check-in status management
* Prevent duplicate check-ins
* Staff/authorized-user validation
* Check-in tracking

Certificate Management

* Generate certificates
* Validate attendee eligibility
* Event completion validation
* Certificate retrieval
* Certificate information management

Feedback Management

* Submit feedback
* Speaker feedback
* Session feedback
* Rating validation from 1 to 5
* Prevent duplicate feedback
* Validate attendee registration
* Validate event ownership
* Check-in validation before feedback submission
* Retrieve event feedback
* Retrieve speaker ratings

Audit Logging

The system maintains audit logs for important operations.

Audit logs contain:

* User ID
* Action
* Entity type
* Entity ID
* Description
* Created timestamp

Audit logs help track important system activities and provide an operational history.

Project Structure

event-conference-management/
│
├── app/
│   ├── models/
│   │   ├── attendee.py
│   │   ├── audit_log.py
│   │   ├── certificate.py
│   │   ├── checkin.py
│   │   ├── event.py
│   │   ├── feedback.py
│   │   ├── hall.py
│   │   ├── notification.py
│   │   ├── payment.py
│   │   ├── purchase.py
│   │   ├── registration.py
│   │   ├── session.py
│   │   ├── session_booking.py
│   │   ├── speaker.py
│   │   ├── ticket.py
│   │   ├── ticket_purchase.py
│   │   ├── user.py
│   │   └── venue.py
│   │
│   ├── repositories/
│   │   ├── attendee_repository.py
│   │   ├── audit_log_repository.py
│   │   ├── event_repository.py
│   │   ├── feedback_repository.py
│   │   ├── hall_repository.py
│   │   ├── notification_repository.py
│   │   ├── payment_repository.py
│   │   ├── registration_repository.py
│   │   ├── session_repository.py
│   │   ├── speaker_repository.py
│   │   ├── ticket_repository.py
│   │   ├── ticket_purchase_repository.py
│   │   └── venue_repository.py
│   │
│   ├── routes/
│   │   ├── attendees.py
│   │   ├── audit_logs.py
│   │   ├── auth.py
│   │   ├── certificates.py
│   │   ├── checkin.py
│   │   ├── events.py
│   │   ├── feedback.py
│   │   ├── notifications.py
│   │   ├── payments.py
│   │   ├── registrations.py
│   │   ├── sessions.py
│   │   ├── speakers.py
│   │   ├── tickets.py
│   │   ├── ticket_purchases.py
│   │   └── venues.py
│   │
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   ├── database.py
│   └── main.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_attendees.py
│   ├── test_certificates.py
│   ├── test_checkin.py
│   ├── test_events.py
│   ├── test_feedback.py
│   ├── test_notifications.py
│   ├── test_payments.py
│   ├── test_registrations.py
│   ├── test_sessions.py
│   ├── test_speakers.py
│   ├── test_tickets.py
│   ├── test_ticket_purchases.py
│   └── test_venues.py
│
├── alembic.ini
├── requirements.txt
├── event_conference.db
└── README.md

Installation

Prerequisites

Make sure the following are installed:

* Python 3.10 or higher
* pip
* Git, if required

Check Python version:

python --version

Create Virtual Environment

Windows PowerShell:

python -m venv venv

Activate the virtual environment:

.\venv\Scripts\Activate.ps1

If PowerShell execution policy prevents activation, use:

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Then activate again:

.\venv\Scripts\Activate.ps1

Install Dependencies

Install all required packages:

pip install -r requirements.txt

Database

The project uses SQLite as the database.

The main database file is:

event_conference.db

SQLAlchemy is used for database interaction and Alembic is included for database migrations.

Run the Application

Start the FastAPI application using Uvicorn:

uvicorn app.main:app --reload

The application will be available at:

http://127.0.0.1:8000

API Documentation

FastAPI automatically provides Swagger UI.

Swagger UI:

http://127.0.0.1:8000/docs

ReDoc:

http://127.0.0.1:8000/redoc

Health Check

The application provides a health-check endpoint:

GET /health

Expected response:

{
"status": "healthy"
}

Root Endpoint

GET /

Expected response:

{
"message": "Event & Conference Management System API",
"version": "1.0.0",
"status": "running"
}

Authentication Flow

1. Register a user using the registration endpoint.
2. Login using the registered email and password.
3. Receive an access token and refresh token.
4. Use the access token in the Authorization header.
5. Access protected endpoints based on the user's role.
6. Use the refresh token when a new access token is required.

Authorization Header

Protected endpoints require:

Authorization: Bearer <access_token>

Testing

The project uses Pytest for automated testing.

Run all tests:

pytest -q

The completed test suite contains 126 passing tests.

Latest successful test result:

126 passed

The tests cover authentication, events, venues, halls, speakers, registrations, tickets, ticket purchases, payments, notifications, sessions, check-in, certificates, feedback, attendees, and related validation and authorization scenarios.

Test Database

The test configuration uses a separate SQLite database:

test_event_conference.db

The test database is created automatically during the test session and is removed after the test session when possible.

API Modules

The application exposes API modules for:

* Authentication
* Events
* Venues
* Halls
* Speakers
* Attendees
* Registrations
* Tickets
* Ticket Purchases
* Payments
* Notifications
* Sessions
* Check-in
* Certificates
* Feedback
* Audit Logs

Architecture

The application follows a layered architecture.

Routes

Routes handle HTTP requests, authentication dependencies, request validation, and API responses.

Schemas

Schemas define request and response structures using Pydantic.

Services

Services contain business logic, authorization rules, validations, and workflow operations.

Repositories

Repositories handle database queries and persistence operations.

Models

Models define SQLAlchemy database tables and relationships.

Database

The database layer manages SQLAlchemy sessions and database configuration.

Security

The application implements:

* JWT-based authentication
* Password hashing
* Access tokens
* Refresh tokens
* Refresh-token revocation
* Role-based access control
* Active-account validation
* Protected API endpoints
* Input validation

Validation and Business Rules

The system includes validation for:

* Duplicate email addresses
* Invalid user roles
* Inactive users
* Invalid event dates
* Invalid registration dates
* Invalid event capacity
* Invalid ticket dates
* Invalid ticket quantities
* Invalid payment information
* Duplicate registrations
* Invalid event registrations
* Unauthorized resource access
* Duplicate attendee profiles
* Duplicate feedback
* Invalid feedback ratings
* Feedback without check-in
* Invalid session assignments
* Invalid speaker assignments
* Duplicate check-ins

Database Migrations

Alembic is configured for database migration management.

Common commands:

Check current migration:

alembic current

View migration history:

alembic history

View migration heads:

alembic heads

Create a new migration:

alembic revision --autogenerate -m "migration message"

Apply migrations:

alembic upgrade head

Downgrade one migration:

alembic downgrade -1

Important Note

The application and automated test suite are currently functional, with the latest test run passing 126 tests. The local SQLite database migration version may need synchronization with the latest Alembic head if the database was created or modified using an earlier migration state.

Submission Checklist

Before submitting the project, verify:

* Application starts successfully
* Swagger documentation opens
* Health endpoint works
* Authentication works
* Role-based access works
* Event APIs work
* Venue and hall APIs work
* Speaker APIs work
* Attendee APIs work
* Registration APIs work
* Ticket APIs work
* Ticket purchase APIs work
* Payment APIs work
* Notification APIs work
* Session APIs work
* Check-in APIs work
* Certificate APIs work
* Feedback APIs work
* Audit log APIs work
* Automated tests pass
* ER diagram is included
* README is included
* requirements.txt is included
* Alembic configuration is included

Running the Project

Quick start:

python -m venv venv

.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn app.main:app --reload

Then open:

http://127.0.0.1:8000/docs

Run tests:

pytest -q

Project Status

The Event & Conference Management System implements the major required event-management workflows with REST APIs, authentication, authorization, database models, business logic, validation, automated tests, notifications, audit logging, and supporting event operations.

Latest automated test status:

126 passed
