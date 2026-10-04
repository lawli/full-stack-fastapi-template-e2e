# User list: negative `skip` or `limit` is inside the declared schema but is passed unchecked to SQL

- Status: **reproduced for `limit=-1`** on 2026-10-04 (apitest 0.2.4rc1, profile `local`).
  `skip=-1` is **not yet reproduced**: the case stops at its first failing step, so that request
  was not sent.
- Endpoint: `GET /api/v1/users/`
- Source commit: `1762adac607a1b29cfc4da129557780beea71616`
- Coverage row: `api|GET|/api/v1/users/|boundary|negative-skip-or-limit-within-declared-schema`
- Case: `tests/api/users-admin/case_list-users-accepts-negative-skip-and-limit--r49yuk.yaml`
- Marker in the case: step `list users with limit -1`, `at: status`

## Contract

- `backend/app/api/routes/users.py:37` declares `skip: int = 0, limit: int = 100` with no lower bound.
- `frontend/src/client/types.gen.ts:478` and `:482` publish both as plain `number` query parameters.
- `backend/app/api/routes/users.py:35` declares `response_model=UsersPublic`;
  `frontend/src/client/types.gen.ts:500` publishes `200: UsersPublic`.
- The only other response the API document publishes for this operation is `422` for a request that
  fails validation (`frontend/src/client/types.gen.ts:491`).

## Why the expected response follows from the declared contract

`limit=-1` and `skip=-1` are integers, so they satisfy the declared parameter types and the
published `422` does not apply. For a request that passes validation and comes from a superuser, the
route declares one answer: `200` with a `UsersPublic` body (`data` array, integer `count`). The case
asserts exactly that and nothing about which users are returned.

## Implementation

- `backend/app/api/routes/users.py:45`-`47` builds
  `select(User).order_by(...).offset(skip).limit(limit)` from the unchecked values and
  `users.py:48` executes it.
- The database is PostgreSQL (`backend/app/core/config.py:31`), which rejects a negative `LIMIT`.
- The application registers no exception handler (`backend/app/main.py:21`-`36`), so the database
  error surfaces as an unhandled server error.

## Reproduction

| | |
|---|---|
| Request | `GET /api/v1/users/?limit=-1` with the superuser's bearer token |
| Expected | `200`, body `UsersPublic` |
| Actual | `500`, body `Internal Server Error` |
| Server log | `sqlalchemy.exc.DataError: (psycopg.errors.InvalidRowCountInLimitClause) LIMIT must not be negative` |

## Still not verified

- `skip=-1`. The second step of the case sends it, but it runs only once the `limit=-1` step passes.
  Observing it now would need a separate case.
- Whether the fix is to answer `200` for negative values or to declare a lower bound (which would
  make `422` the declared answer and require the case to change) is the owner's decision.
