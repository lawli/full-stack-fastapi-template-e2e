# Own-profile update: an explicit `null` email is inside the declared schema but is written to a non-null column

- Status: **reproduced** on 2026-10-04 (apitest 0.2.4rc1, profile `local`).
- Endpoint: `PATCH /api/v1/users/me`
- Source commit: `1762adac607a1b29cfc4da129557780beea71616`
- Coverage row: `api|PATCH|/api/v1/users/me|boundary|explicit-null-email-within-declared-schema`
- Case: `tests/api/users-me/case_update-me-accepts-explicit-null-email--f1iwcj.yaml`
- Marker in the case: step `update the own profile with an explicit null email`, `at: status`

## Contract

- `backend/app/models.py:43` declares `UserUpdateMe.email` as `EmailStr | None`;
  `frontend/src/client/types.gen.ts:300` publishes it as `email?: string | null`.
- `backend/app/api/routes/users.py:81` declares `response_model=UserPublic`;
  `frontend/src/client/types.gen.ts:582` publishes `200: UserPublic`.
- `UserPublic.email` is a required string (`backend/app/models.py:15`, `:63`;
  `frontend/src/client/types.gen.ts:222`).
- The only other response the API document publishes for this operation is `422` for a body that
  fails validation (`frontend/src/client/types.gen.ts:573`).

## Why the expected response follows from the declared contract

`{"email": null}` satisfies the declared request model, so the published `422` does not apply. For
a valid body from an authenticated user, the route declares one answer: `200` with the caller's
`UserPublic`, in which `email` is a string. The case asserts the status, that `id` is the caller's
id and that `email` is a string. It does not assert which email is returned, because the contract
does not say what an explicit `null` means.

## Implementation

- `backend/app/api/routes/users.py:89` skips the duplicate check when the email is falsy.
- `backend/app/api/routes/users.py:95` takes every field the client sent
  (`model_dump(exclude_unset=True)`), which includes `email: None`, and `users.py:96`-`98` copies it
  onto the stored user and commits.
- The `email` column is not nullable (`backend/app/models.py:15` on the table model at `:52`;
  `backend/app/alembic/versions/e2412789c190_initialize_models.py:23`).
- The application registers no exception handler (`backend/app/main.py:21`-`36`), so the constraint
  violation raised by the commit surfaces as an unhandled server error.

## Reproduction

| | |
|---|---|
| Request | `PATCH /api/v1/users/me`, body `{"email": null}`, with the bearer token of a user the case signed up |
| Expected | `200`, body `UserPublic` with a string `email` |
| Actual | `500`, body `Internal Server Error` |
| Server log | `psycopg.errors.NotNullViolation: null value in column "email" of relation "user" violates not-null constraint` |

The case's teardown then deleted the user (`200`).

## Still not verified

Whether `null` should mean "leave unchanged" (answer `200`) or should be removed from the schema
(answer `422`, and the case changes) is the owner's decision.
