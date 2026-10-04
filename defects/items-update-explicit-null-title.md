# Item update: an explicit `null` title is inside the declared schema but is written to a non-null column

- Status: **reproduced** on 2026-10-04 (apitest 0.2.4rc1, profile `local`).
- Endpoint: `PUT /api/v1/items/{id}`
- Source commit: `1762adac607a1b29cfc4da129557780beea71616`
- Coverage row: `api|PUT|/api/v1/items/{id}|boundary|explicit-null-title-within-declared-schema`
- Case: `tests/api/items/case_update-item-accepts-explicit-null-title--x08gl1.yaml`
- Marker in the case: step `update the item with an explicit null title`, `at: status`

## Contract

- `backend/app/models.py:86` declares `ItemUpdate.title` as `str | None`;
  `frontend/src/client/types.gen.ts:94` publishes it as `title?: string | null`.
- `backend/app/api/routes/items.py:75` declares `response_model=ItemPublic`;
  `frontend/src/client/types.gen.ts:919` publishes `200: ItemPublic`.
- `ItemPublic.title` is a required string (`backend/app/models.py:75`, `:104`;
  `frontend/src/client/types.gen.ts:68`).
- The only other response the API document publishes for this operation is `422` for a request that
  fails validation (`frontend/src/client/types.gen.ts:910`).

## Why the expected response follows from the declared contract

`{"title": null}` satisfies the declared request model, so the published `422` does not apply. For
a valid body from the item's owner, the route declares one answer: `200` with that item's
`ItemPublic`, in which `title` is a string. The case asserts the status, that `id` is the item's id
and that `title` is a string. It does not assert which title is returned, because the contract
does not say what an explicit `null` means.

## Implementation

- `backend/app/api/routes/items.py:91` takes every field the client sent
  (`model_dump(exclude_unset=True)`), which includes `title: None`, and `items.py:92`-`94` copies
  it onto the stored item and commits.
- The `title` column is not nullable (`backend/app/models.py:75` on the table model at `:91`;
  `backend/app/alembic/versions/e2412789c190_initialize_models.py:38`).
- The application registers no exception handler (`backend/app/main.py:21`-`36`), so the constraint
  violation raised by the commit surfaces as an unhandled server error.

## Reproduction

| | |
|---|---|
| Request | `PUT /api/v1/items/<id of an item the case created>`, body `{"title": null}`, with the owner's bearer token |
| Expected | `200`, body `ItemPublic` with a string `title` |
| Actual | `500`, body `Internal Server Error` |
| Server log | `psycopg.errors.NotNullViolation: null value in column "title" of relation "item" violates not-null constraint` |

The case's teardown then deleted the item and its owner (`200` each).

## Still not verified

Whether `null` should mean "leave unchanged" (answer `200`) or should be removed from the schema
(answer `422`, and the case changes) is the owner's decision.
