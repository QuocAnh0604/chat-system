# AI Development Rules

## Architecture

Layered Architecture

Router

↓

Service

↓

Repository

↓

Database

Business logic only exists in Service.

Repository only communicates with the database.

Router never accesses the database directly.

## Technology

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- JWT

## Coding Style

- Use type hints.
- Use async.
- Use UUID.
- Follow PEP8.
- Prefer early return.

## Database

Every table uses UUID primary key.

Use created_at and updated_at.

Foreign keys should define ondelete behavior.

## Goal

Write maintainable and production-ready code.

Explain design decisions before writing complex code.