# Private user creation: the request accepts any string as email, the response requires an email address

- Status: suspected from reading the source; **not yet reproduced** (no request was sent).
- Endpoint: `POST /api/v1/private/users/` (registered only when `FASTAPI_ENV` is `development`,
  `backend/app/api/main.py:13`-`14`)
- Source commit: `1762adac607a1b29cfc4da129557780beea71616`
- Coverage row: `api|POST|/api/v1/private/users/|validation|email-format-not-enforced-by-request-model`
  (status `blocked`; no case was written, see below)

## Contract

- Request: `backend/app/api/routes/private.py:17` declares `PrivateUserCreate.email` as a plain
  `str`; `frontend/src/client/types.gen.ts:146` publishes it as `email: string`. A body whose email
  is, for example, `not-an-email` passes the declared request schema.
- Response: `backend/app/api/routes/private.py:23` declares `response_model=UserPublic`, whose
  `email` is an email address (`backend/app/models.py:15`, `:63`);
  `frontend/src/client/types.gen.ts:944` publishes `200: UserPublic` and `:935` publishes `422`.

The two declarations disagree about such a body: the request side accepts it, the response side
cannot represent it. The contract does not say which side is intended.

## Implementation

- `backend/app/api/routes/private.py:29`-`33` builds the stored user directly from the body without
  validating the email, and `private.py:35`-`36` commits it.
- `backend/app/api/routes/private.py:38` returns that user through the declared response model, so
  a non-email string would fail response validation after the row was already stored.
- The application registers no exception handler (`backend/app/main.py:21`-`36`), so that failure
  would surface as an unhandled server error, which is neither of the declared answers.
- A stored row with a non-email value would also affect another route:
  `backend/app/api/routes/users.py:50` validates every listed row as `UserPublic`, so
  `GET /api/v1/users/` could fail for every caller while the row is on the requested page.

Under either reading of the contract the implementation conflicts with it: if the body is meant to
be accepted, the route cannot produce the declared `200`; if it is meant to be rejected, the route
does not reject it and stores the row.

## Why there is no case

- The expected status (`200` or `422`) cannot be chosen from the contract, so it would have to be
  invented.
- Executing the request is risky for the environment: if the row is stored, the user list may stay
  broken until the row is removed, and the response would carry no id to delete it by. The only
  API path left for cleanup is to log in as that user and call `DELETE /api/v1/users/me`.

## Input needed

1. The intended behavior for a non-email string on this route.
2. Permission to execute the scenario against the reference environment, or a disposable
   environment for it.

## Not verified

The response of the running service, and whether `GET /api/v1/users/` actually fails with such a
row present.
