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

* Redis

### Async Processing

* Celery
* Celery Beat

### Deployment

* Docker
* Nginx
* Gunicorn
* AWS EC2

### Documentation

* Swagger / OpenAPI

### Version Control

* Git
* GitHub

---

## Current Features

### Foundation

* Environment Variables
* PostgreSQL Integration
* Health Check API

### Multi-Tenancy

* Organization Model
* Organization CRUD API

---

## Planned Features

### User Management

* Custom User Model
* Organization-based Users
* User Profiles

### Authentication & Authorization

* JWT Authentication
* Role-Based Access Control (RBAC)

Roles:

* Admin
* Manager
* Employee

### Departments

* Department CRUD
* User Assignment

### Workflow Management

* Workflow Templates
* Dynamic Approval Chains
* Workflow Execution Engine

### Approval System

* Approve Requests
* Reject Requests
* Reassign Requests

### Notifications

* Email Notifications
* Scheduled Reminders

### Audit Logs

Track:

* Who performed an action
* Previous value
* New value
* Timestamp

### Dashboard APIs

* Pending Approvals
* Completed Approvals
* User Metrics
* Department Metrics

### Performance Optimization

* Redis Caching
* Database Indexing
* Query Optimization

### Deployment

* Docker
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
