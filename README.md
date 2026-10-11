# TaskFlow — Task Management REST API

A small REST API for managing tasks, built with Python, Flask, Flask-SQLAlchemy and SQLite, with an automated pytest test suite.

I built this as a learning and portfolio project to practise backend fundamentals: REST API design, a database layer with an ORM, input validation, consistent error handling and automated testing.

[![Tests](https://github.com/zunairaiftikh/taskflow-rest-api/actions/workflows/tests.yml/badge.svg)](https://github.com/zunairaiftikh/taskflow-rest-api/actions/workflows/tests.yml)

## Objectives

- Design a clean REST API with the correct HTTP methods and status codes.
- Store data in SQLite through the SQLAlchemy ORM.
- Validate all input and return clear, consistent JSON errors.
- Verify behaviour with automated tests that never touch the development database.

## Features

- Create, list, retrieve, partially update and delete tasks.
- Filter tasks by status (`GET /api/tasks?status=pending`).
- Request validation: missing or blank titles, invalid statuses, unsupported fields, malformed JSON.
- Consistent JSON error responses for every error, including unknown URLs and unexpected server errors (no stack traces are returned to clients).
- UTC timestamps for creation and last update.
- - 32 automated tests using pytest and Flask's test client, run automatically on every push with GitHub Actions.

## Technology stack

- Python
- Flask (application factory and blueprints)
- Flask-SQLAlchemy / SQLAlchemy
- SQLite
- pytest

Exact versions are pinned in `requirements.txt`. The project was developed and tested on Windows with Python 3.14.7.

## Project structure

```
TaskFlow/
├── app/
│   ├── __init__.py      # Application factory (create_app)
│   ├── errors.py        # Global JSON error handlers
│   ├── extensions.py    # SQLAlchemy extension object
│   ├── models.py        # Task model
│   └── routes.py        # API endpoints and validation helpers
├├── tests/
│   ├── conftest.py          # Test fixtures (app and client, in-memory database)
│   ├── test_tasks.py        # 26 tests: endpoints and error handling
│   └── test_edge_cases.py   # 6 tests: edge cases and extra validation
├── .github/workflows/tests.yml   # GitHub Actions: runs the tests on every push
├── .gitignore
├── requirements.txt
└── README.md
```

The development database is created automatically at `instance/taskflow.db` and is excluded from Git.

## Installation (Windows, Command Prompt)

```
git clone https://github.com/zunairaiftikh/taskflow-rest-api.git
cd taskflow-rest-api
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

When the virtual environment is active, your prompt starts with `(.venv)`.

## Database initialization

There is nothing to run manually. The tables are created automatically when the application starts, and the SQLite file is stored at `instance/taskflow.db`.

## Running the application

```
flask --app app run --debug
```

The API is then available at `http://127.0.0.1:5000`. Stop it with `Ctrl+C`. The `--debug` flag is for local development only.

Check that it is running:

```
curl http://127.0.0.1:5000/health
```

## API reference

Base URL: `http://127.0.0.1:5000`

| Method | URL | Description | Success |
|---|---|---|---|
| GET | `/health` | Health check | 200 |
| POST | `/api/tasks` | Create a task | 201 |
| GET | `/api/tasks` | List tasks (optional `?status=`) | 200 |
| GET | `/api/tasks/<id>` | Get one task | 200 |
| PATCH | `/api/tasks/<id>` | Partially update a task | 200 |
| DELETE | `/api/tasks/<id>` | Delete a task | 200 |

Allowed statuses: `pending` (default), `in_progress`, `completed`.

Timestamps are UTC in ISO 8601 format with second precision, for example `2026-10-10T09:22:24Z`.

### Task object

```json
{
  "id": 1,
  "title": "Learn Flask",
  "description": "Finish TaskFlow",
  "status": "pending",
  "created_at": "2026-10-10T09:22:24Z",
  "updated_at": "2026-10-10T09:22:24Z"
}
```

### Create a task

`POST /api/tasks` accepts `title` (required) and `description` (optional). New tasks always start as `pending`.

```
curl -X POST http://127.0.0.1:5000/api/tasks -H "Content-Type: application/json" -d "{\"title\": \"Learn Flask\", \"description\": \"Finish TaskFlow\"}"
```

Response `201 Created`: the task object shown above.

### List tasks

```
curl http://127.0.0.1:5000/api/tasks
curl "http://127.0.0.1:5000/api/tasks?status=pending"
```

Response `200 OK`:

```json
{
  "count": 1,
  "tasks": [
    {
      "id": 1,
      "title": "Learn Flask",
      "description": "Finish TaskFlow",
      "status": "pending",
      "created_at": "2026-10-10T09:22:24Z",
      "updated_at": "2026-10-10T09:22:24Z"
    }
  ]
}
```

An invalid status such as `?status=done` returns `400`.

### Get one task

```
curl http://127.0.0.1:5000/api/tasks/1
```

### Update a task

`PATCH /api/tasks/<id>` changes only the fields you send. Supported fields: `title`, `description` (may be `null` to clear it) and `status`.

```
curl -X PATCH http://127.0.0.1:5000/api/tasks/1 -H "Content-Type: application/json" -d "{\"status\": \"in_progress\"}"
```

All fields are validated before anything is saved, so an invalid request changes nothing.

### Delete a task

```
curl -X DELETE http://127.0.0.1:5000/api/tasks/1
```

Response `200 OK`:

```json
{
  "id": 1,
  "message": "Task 1 deleted"
}
```

## Validation and error handling

Every error is a JSON object with an `error` message:

```json
{
  "error": "Invalid status 'done'. Allowed values: pending, in_progress, completed"
}
```

| Status | When it happens |
|---|---|
| 400 Bad Request | Body is not a JSON object or is malformed; `title` missing, blank, not a string, or longer than 200 characters; `description` not a string or null; invalid status; unsupported field; empty PATCH body |
| Task id does not exist (including ids too large to store), or the URL does not exist. |
| 405 Method Not Allowed | The HTTP method is not supported for that URL |
| 500 Internal Server Error | Unexpected failure. The client sees only a generic message; details are logged on the server |

Rules in detail:

- `title` is trimmed of surrounding spaces and must contain at least one character.
- `POST` accepts only `title` and `description`. `PATCH` accepts only `title`, `description` and `status`. Unknown fields are rejected, not silently ignored.

## Running the tests

With the virtual environment active:

```
python -m pytest -v
```

Tests use Flask's test client and a fresh in-memory SQLite database for every test, so they never read or change `instance/taskflow.db`.

### Test summary

The suite contains 32 tests. All 32 passed in a local run on Windows with Python 3.14.7, and the same suite runs on GitHub Actions (Ubuntu, Python 3.14) on every push to `main`. It covers:

- Health check (1)
- Creating tasks: success and validation failures (5)
- Listing and filtering, including an invalid filter value (4)
- Retrieving a task, a missing task and a non-numeric id (3)
- Updating tasks: success, clearing the description, invalid and unsupported input, malformed JSON, missing task, and a check that a failed update changes nothing (8)
- Deleting tasks: success, only the requested task removed, missing task (3)
 - Edge cases in `test_edge_cases.py`: a task id too large for SQLite returns 404, overlong titles on create and update, a non-string description, a JSON list as the body, and a null status on update (6)

A code coverage percentage has not been measured.

## Current limitations

- No authentication or user accounts; anyone who can reach the API can modify tasks.
- No pagination, sorting or search.
- Uses Flask's development server and a local SQLite file; it is not set up for production deployment.
- Database tables are created automatically at startup; there are no schema migrations.
- Timestamps have one-second precision.

## Future improvements

- Pagination, sorting and search by title
- Database migrations (for example with Flask-Migrate)
- Authentication
- Docker support

## License

No license has been added yet. Without one, the code is publicly visible but others have no explicit permission to reuse it. Choose one deliberately (for example MIT, a common choice for portfolio projects) before adding it.