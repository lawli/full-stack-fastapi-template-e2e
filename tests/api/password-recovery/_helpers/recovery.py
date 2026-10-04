"""Read the password-reset token of a case-owned user.

The token only ever appears inside HTML, which a declarative `extract` cannot parse.
The helper only reads. Helper args are literal, so it names the ctx value to use
instead of carrying it.
"""

from __future__ import annotations

import re
from typing import Any

# Link built in backend/app/utils.py:73: <FRONTEND_HOST>/reset-password?token=<jwt>
_RESET_LINK = re.compile(r"reset-password\?token=([A-Za-z0-9_.\-]+)")


def reset_token_from_mail(http: Any, ctx: Any, email_key: str = "user_email") -> dict[str, str]:
    """Token from the recovery mail the catcher holds for the case-owned address.

    Uses the two catcher calls the repository's own end-to-end helper uses
    (frontend/tests/utils/mailpit.ts:20, 30): search by recipient, then view the HTML.
    """
    found = http.get(
        "mailpit", "/api/v1/search", params={"query": f"to:{getattr(ctx, email_key)}", "limit": 1}
    )
    if found.status_code != 200:
        raise RuntimeError(f"mail search answered HTTP {found.status_code}")
    messages = found.json()["messages"]
    if not messages:
        raise RuntimeError("no recovery mail captured for the case-owned address")
    html = http.get("mailpit", f"/view/{messages[0]['ID']}.html")
    if html.status_code != 200:
        raise RuntimeError(f"mail HTML view answered HTTP {html.status_code}")
    match = _RESET_LINK.search(html.text)
    if match is None:
        raise RuntimeError("no reset-password link found in the recovery mail")
    return {"reset_token": match.group(1)}
