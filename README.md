# full-stack-fastapi-template-e2e

API end-to-end tests for
[full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template),
generated with [repo2test](https://github.com/lawli/repo2test) 0.2.4 as a demonstration. An
agent following the pinned workspace skill wrote the coverage inventory, the cases and the
defect notes. They are published as generated.

| | |
|---|---|
| Source reference | full-stack-fastapi-template at commit `1762ada` |
| Inventory (`coverage/`) | 28 endpoints, 148 behaviors |
| Cases (`tests/`) | 90, covering 144 behaviors |
| Not authored | 2 behaviors blocked, 2 recorded as gaps |
| Last local run | 84 passed, 6 expected failures |

- **Expected failures** reproduce places where the service and its declared request and
  response models disagree. `defects/` has one note per conflict: 7 notes, 6 reproduced by a
  case and 1 based on the source only.
- **Pending expectations:** 71 of the 144 authored behaviors are pending. The repository
  declares no contract for them, so a passing case there does not count as verified.

## Run it

1. Start the backend at the reference commit together with its database and a Mailpit
   instance, as the template's development guide describes.
2. In this repository, create `.env` with the variables that `profiles/local.yaml` references:

   ```sh
   LOCAL_API_URL=<backend base URL>
   LOCAL_MAILPIT_URL=<Mailpit base URL>
   LOCAL_API_SUPERUSER_EMAIL=<first superuser email>
   LOCAL_API_SUPERUSER_PASSWORD=<first superuser password>
   ```

3. Run the suite:

   ```sh
   uv sync --locked
   uv run --locked apitest run --service api --profile local --report both
   ```

The cases create and delete their own records. Run them only against a disposable instance.
Each run leaves 11 messages in Mailpit, which the cases cannot delete.

## Workspace setup

Run `uv sync --locked`, then `uv run --locked apitest --help`.
Configure service URLs with `apitest workspace configure`; environment values stay local.
Install the entry with `python3 tools/install_entry.py --host codex` or `--host claude`.
Use `--update` to deliberately replace an installed entry. For sibling workspace access, start Codex with `--add-dir <workspace> --add-dir "$(uv cache dir)"` (add `-c sandbox_workspace_write.network_access=true` when uv must download packages); start Claude Code with `--add-dir <workspace>`.

Platform setup: require the validate check and up-to-date branches or a merge queue/train; require CODEOWNERS approval by a runner maintainer other than the PR author for wheel/lock changes. Enable the default-branch push check. These platform settings must be configured by a repository administrator; generating YAML does not enforce them.
