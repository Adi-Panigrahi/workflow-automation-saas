# Workflow Automation SaaS

A production-style multi-tenant Workflow Automation Platform built with Django and Django REST Framework.

The goal of this project is to simulate a real enterprise SaaS application where organizations can manage users, departments, approval workflows, and automated business processes.

---

## Project Objective

Many organizations still manage approvals through emails, spreadsheets, and manual processes.

This platform aims to automate workflows such as:

* Leave Requests
* Expense Claims
* Laptop Requests
* Purchase Requests
* Access Requests

Example Workflow:

Employee → Manager Approval → HR Approval → Completed

---

## Tech Stack

### Backend

* Python
* Django
* Django REST Framework

### Database

* PostgreSQL

### Authentication

* JWT Authentication

### Caching

* Redis — planned

### Async Processing

* Celery — planned
* Celery Beat — planned

### Deployment

* Docker and Docker Compose — development environment implemented
* Nginx — planned
* Gunicorn — planned
* AWS EC2 — planned

### Documentation

* Swagger / OpenAPI — planned

### Version Control

* Git
* GitHub

---

## Current Features

### Foundation

* Environment Variables
* PostgreSQL Integration
* Health Check API
* Dockerized Django and PostgreSQL development environment
* Persistent PostgreSQL Docker volume and health-checked service startup

### Multi-Tenancy

* Organization Model
* Authenticated, tenant-scoped organization access
* Organization-level users, departments, workflow templates, instances, approvals, and audit logs

### Identity and Authorization

* Custom email-based user model
* JWT login and token refresh
* Admin, Manager, and Employee roles
* Tenant-scoped user management for organization admins

### Workflow Engine

* Configurable workflow templates and ordered approval steps
* Per-template required request-data schema
* Explicit step approvers validated against tenant and role
* Structured request data stored with every workflow instance
* Atomic workflow start, progression, reassignment, rejection, cancellation, and completion
* Immutable submitted requests with tenant-scoped visibility
* Database constraints preventing duplicate step orders and approval transitions
* Locked workflow templates after first use, with safe cloning for future revisions

### Notifications

* In-app notifications for approval assignments, reassignments, approvals, and rejections
* Recipient-only notification inbox with read/unread tracking

### Auditability

* Append-only audit records for workflow starts, approvals, reassignments, rejections, and cancellations
* Read-only audit-log API for organization admins

## API Overview

All protected endpoints require a JWT access token:

```text
Authorization: Bearer <access-token>
```

```text
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/

GET/POST /api/auth/users/
GET/POST /api/departments/
GET/POST /api/workflows/
POST     /api/workflows/{id}/clone/
GET/POST /api/workflow-steps/

GET/POST /api/workflow-instances/
POST     /api/workflow-instances/{id}/cancel/
GET      /api/workflow-instances/{id}/timeline/
GET      /api/workflow-instances/analytics/   # organization admins
GET      /api/approvals/
POST     /api/approvals/{id}/approve/
POST     /api/approvals/{id}/reject/
POST     /api/approvals/{id}/reassign/
GET      /api/notifications/?unread=true
POST     /api/notifications/{id}/mark_read/
POST     /api/notifications/mark_all_read/
GET      /api/audit-logs/
```

## Run Locally with Docker

### Prerequisites

* Docker Desktop
* A `.env` file containing `SECRET_KEY`, `DEBUG`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`

### Start the application

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py check
docker compose exec web python manage.py test
```

The API is available at:

```text
http://localhost:8000/api/health/
```

The Django admin is available at:

```text
http://localhost:8000/admin/
```

### Useful Docker commands

```bash
# Show service status
docker compose ps

# Follow Django logs
docker compose logs -f web

# Open a Django shell inside the container
docker compose exec web sh

# Create an admin user
docker compose exec web python manage.py createsuperuser

# Stop services while preserving PostgreSQL data
docker compose down
```

> Do not run `docker compose down -v` unless you intentionally want to delete the Docker PostgreSQL database volume.

## Local Development Without Docker

```bash
source venv/bin/activate
python manage.py migrate
python manage.py test
python manage.py runserver
```

---

## Planned Features

### User Management

* User profiles

### Authentication & Authorization

* Advanced RBAC policies

Roles:

* Admin
* Manager
* Employee

### Departments

* Department-level reporting hierarchy

### Workflow Management

* Advanced conditional workflow routing

### Approval System

* Escalation policies
* Delegation rules

### Notifications

* Email Notifications
* Scheduled Reminders

### Audit Logs

Track:

* Retention and archival policy

### Dashboard APIs

* Advanced team and department analytics

### Performance Optimization

* Redis Caching
* Database Indexing
* Query Optimization

### Deployment

* AWS EC2
* Nginx
* Gunicorn

---

## Learning Goals

This project is being built to gain hands-on experience with:

* Backend Engineering
* API Design
* Database Modeling
* Multi-Tenant Architectures
* Authentication & Authorization
* Distributed Systems Concepts
* Production Deployments

---

## Author

Aditya Panigrahi
