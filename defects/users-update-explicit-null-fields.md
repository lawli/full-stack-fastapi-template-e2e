# User update by id: an explicit `null` is inside the declared schema but is written to non-null columns

- Status: **reproduced for `email`** on 2026-10-04 (apitest 0.2.4rc1, profile `local`). The three
  sibling fields listed below are **not exercised** by a case.
- Endpoint: `PATCH /api/v1/users/{user_id}`
- Source commit: `1762adac607a1b29cfc4da129557780beea71616`
- Coverage row: `api|PATCH|/api/v1/users/{user_id}|boundary|explicit-null-email-within-declared-schema`
- Case: `tests/api/users-admin/case_update-user-accepts-explicit-null-email--qu0g8a.yaml`
- Marker in the case: step `update the user with an explicit null email`, `at: status`

## Contract

- `backend/app/models.py:34` declares `UserUpdate.email` as `EmailStr | None`;
  `frontend/src/client/types.gen.ts:270` publishes it as `email?: string | null`.
- `backend/app/api/routes/users.py:185` declares `response_model=UserPublic`;
  `frontend/src/client/types.gen.ts:722` publishes `200: UserPublic`.
- `UserPublic.email` is a required string (`backend/app/models.py:15`, `:63`;
  `frontend/src/client/types.gen.ts:222`).
- The only other response the API document publishes for this operation is `422` for a request that
  fails validation (`frontend/src/client/types.gen.ts:713`).

## Why the expected response follows from the declared contract

`{"email": null}` satisfies the declared request model, so the published `422` does not apply. For
a valid body from a superuser addressing an existing user, the route declares one answer: `200`
with that user's `UserPublic`, in which `email` is a string. The case asserts the status, that `id`
is the addressed user's id and that `email` is a string. It does not assert which email is
returned, because the contract does not say what an explicit `null` means.

## Implementation

- `backend/app/api/routes/users.py:203` skips the duplicate check when the email is falsy, and
  `users.py:210` hands the body to `crud.update_user`.
- `backend/app/crud.py:21` takes every field the client sent (`model_dump(exclude_unset=True)`),
  which includes `email: None`; `crud.py:27`-`29` copies it onto the stored user and commits.
- The `email` column is not nullable (`backend/app/models.py:15` on the table model at `:52`;
  `backend/app/alembic/versions/e2412789c190_initialize_models.py:23`).
- The application registers no exception handler (`backend/app/main.py:21`-`36`), so the constraint
  violation raised by the commit surfaces as an unhandled server error.

## Reproduction

| | |
|---|---|
| Request | `PATCH /api/v1/users/<id of a user the case signed up>`, body `{"email": null}`, with the superuser's bearer token |
| Expected | `200`, body `UserPublic` with a string `email` |
| Actual | `500`, body `Internal Server Error` |
| Server log | `psycopg.errors.NotNullViolation: null value in column "email" of relation "user" violates not-null constraint` |

The case's teardown then deleted the user (`200`).

## Same pattern, not exercised by a case (still suspected)

`UserUpdate` declares three more fields as nullable whose targets do not accept `null`; the same
lines apply to them:

- `is_active` (`backend/app/models.py:35`) and `is_superuser` (`models.py:36`): non-null columns
  (`e2412789c190_initialize_models.py:24`, `:25`).
- `password` (`backend/app/models.py:38`): `backend/app/crud.py:23`-`25` hashes the value whenever
  the key is present, including `None`.

## Still not verified

Whether `null` should mean "leave unchanged" (answer `200`) or should be removed from the schema
(answer `422`, and the case changes) is the owner's decision.
