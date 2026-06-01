"""Stubbed real-platform adapters.

Each is a :class:`StubAdapter`: it documents what a contributor needs to wire up
(upload path, re-fetch path, auth), but raises ``NotImplementedError`` until
someone implements it with real credentials. The ``notes`` field captures the
known/expected mechanics so the stub is a useful starting point.

NONE of these contain credentials. All auth must come from environment variables
(see ``.env.example``). The matrix's value is crowd-maintained: contributors add
real adapters or simply record observed behavior over time.
"""

from __future__ import annotations

from .base import StubAdapter


class InstagramAdapter(StubAdapter):
    name = "instagram"
    display_name = "Instagram"
    requires_account = True
    notes = (
        "Upload via the Instagram Graph API (Business/Creator account + token) "
        "or the web composer; re-fetch the served media URL. Needs IG_TOKEN."
    )


class XAdapter(StubAdapter):
    name = "x"
    display_name = "X (Twitter)"
    requires_account = True
    notes = (
        "Upload media via the X API v2 media endpoint; re-fetch the pbs.twimg.com "
        "asset. Needs X_BEARER_TOKEN / OAuth creds."
    )


class WhatsAppAdapter(StubAdapter):
    name = "whatsapp"
    display_name = "WhatsApp"
    requires_account = True
    notes = (
        "Send media via the WhatsApp Cloud API and re-download the media id. "
        "Note: heavy transcoding expected. Needs WHATSAPP_TOKEN / phone id."
    )


class RedditAdapter(StubAdapter):
    name = "reddit"
    display_name = "Reddit"
    requires_account = True
    notes = (
        "Submit an image post via the Reddit API; re-fetch the i.redd.it URL. "
        "Needs REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET / refresh token."
    )


class TikTokAdapter(StubAdapter):
    name = "tiktok"
    display_name = "TikTok"
    requires_account = True
    notes = (
        "Upload via the TikTok Content Posting API; re-fetch the served asset. "
        "Primarily video; needs TIKTOK_ACCESS_TOKEN."
    )


class LinkedInAdapter(StubAdapter):
    name = "linkedin"
    display_name = "LinkedIn"
    requires_account = True
    notes = (
        "Upload an image via the LinkedIn Assets/UGC API; re-fetch the served "
        "media. Needs LINKEDIN_ACCESS_TOKEN."
    )


STUB_ADAPTERS = [
    InstagramAdapter,
    XAdapter,
    WhatsAppAdapter,
    RedditAdapter,
    TikTokAdapter,
    LinkedInAdapter,
]
