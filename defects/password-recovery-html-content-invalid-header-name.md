# Recovery HTML preview: the success response carries an invalid header name and is never delivered

- Status: **reproduced** on 2026-10-04 (profile `local`): four times in one run on apitest
  0.2.4rc1, and again on 0.2.4.
- Endpoint: `POST /api/v1/password-recovery-html-content/{email}`
- Source commit: `1762adac607a1b29cfc4da129557780beea71616`
- Coverage row: `api|POST|/api/v1/password-recovery-html-content/{email}|happy|superuser-gets-recovery-html`
- Case: `tests/api/password-recovery/case_recovery-html-content-for-registered-user--jn78u0.yaml`
- Marker in the case: step `get the recovery HTML for the case-owned user`, `at: response`; see
  "How the runner records it".

## Contract

- `backend/app/api/routes/login.py:100`-`104` registers the route with
  `response_class=HTMLResponse` (`:103`); its description is "HTML Content for Password Recovery"
  (`login.py:107`).
- `frontend/src/client/types.gen.ts:466` publishes `200: string` for the operation and
  `frontend/src/client/sdk.gen.ts:91` reads it as text.
- The only other response the API document publishes is `422` for a request that fails validation
  (`frontend/src/client/types.gen.ts:457`).

## Why the expected response follows from the declared contract

The path parameter is a plain string, so the published `422` does not apply. For a superuser asking
about a registered email, the route declares one answer: `200` with an HTML body. The contract is
not silent or ambiguous about this request, so this is a conflict and not a pending expectation.
The case asserts the status, a `text/html` content type and that the body is an HTML document. It
asserts nothing about the wording of the HTML or about any other header.

## Implementation

- `backend/app/api/routes/login.py:121`-`123` returns
  `HTMLResponse(content=..., headers={"subject:": email_data.subject})`. The header name is
  `subject:`, with a colon inside the name.
- A colon is not allowed in an HTTP header name. The server the project pins, uvicorn 0.49.0
  (`uv.lock:1470`-`1471`), checks every response header name when it writes the response head and
  raises `RuntimeError("Invalid HTTP header name.")`
  (`uvicorn/protocols/http/httptools_impl.py:30`, `:496`-`498`). It writes its access-log line with
  the status before that check (`:483`-`491`), so the log shows `200 OK` although nothing is sent.
- Every request that reaches the end of the handler takes this path. Requests that stop earlier do
  answer: without a token (`401`), as a normal user (`403`) and for an unregistered email (`404`).

## Reproduction

| | |
|---|---|
| Request | `POST /api/v1/password-recovery-html-content/<address of a user the case signed up>` with the superuser's bearer token |
| Expected | `200`, `Content-Type: text/html`, an HTML body |
| Actual | No HTTP response. The client reports `Server disconnected without sending a response.` |
| Server log | Access line `200 OK`, then a traceback ending `RuntimeError: Invalid HTTP header name.` |

In the same run the `401`, `403` and `404` paths of this route answered as their cases expect.

## How the runner records it

- The failure is a transport error, not an assertion failure: the business outcome is `ERROR`
  ("EXECUTE error: Server disconnected without sending a response.").
- The case's marker names exactly that result, `at: response` on the step that sends the request,
  so the case is reported as `XFAIL` and no longer fails the run. This location exists since
  apitest 0.2.4; the first reproduction, on 0.2.4rc1, was reported as `ERROR`.
- The marker matches nothing else. If the route answers with a wrong status the case is a `FAIL`,
  and if it answers correctly the case is an `XPASS`, which fails the run and prompts removing the
  marker and this note.

## Effect on other cases

Three reset-password cases used this route in setup to obtain a reset token. They now take the
token from the recovery mail in the local mail catcher instead.

## Still not verified

The behaviour behind a different HTTP server implementation or a reverse proxy.
