# Contributing to c2pa-stripcheck

The whole point of this project is the **crowd-maintained behavior matrix**: a
versioned record of which platforms strip, preserve, re-sign, or soft-bind C2PA
Content Credentials. There are only manual blog anecdotes out there today. Your
contribution makes the matrix more complete and more trustworthy.

There are two ways to contribute, in increasing order of effort.

## 1. Record an observed result (no code)

If you have an account on a platform and can manually upload a signed asset and
download the processed copy, you can verify the result with the tool and report
it:

```bash
# read the manifest before and after upload
uv run c2pa-stripcheck readers          # see which readers you have
# ... upload your-signed.jpg to the platform by hand, download the result ...
```

Then open an issue or PR with:

- platform name,
- date tested,
- the verdict (PRESERVED / STRIPPED / RE-SIGNED / SOFT-BINDING-RECOVERABLE),
- how you verified (c2patool / c2pa-python / Content Credentials Verify site),
- the asset format (JPEG / PNG / MP4 / etc.) — behavior often differs by format.

Please do **not** attach the real asset if it contains personal media. A
description is enough.

## 2. Implement a real adapter (code)

Each platform is a `PlatformAdapter` (see `src/c2pa_stripcheck/adapters/`). The
real adapters in `stubs.py` raise `NotImplementedError` until someone wires them
up. To implement one:

1. Subclass `PlatformAdapter` (not `StubAdapter`).
2. Implement `upload(asset_path) -> UploadHandle` and
   `refetch(handle, dest_dir) -> Path`.
3. Read all credentials from environment variables (see `.env.example`). **Never
   hardcode tokens.**
4. Set `kind = "live"` and `requires_account = True`.
5. Add a test that exercises your adapter against a **mock HTTP server or
   recorded fixtures** — do not require live credentials in CI.

The classifier and matrix are shared, so a correct `upload`/`refetch` pair is all
you need; verdicts come for free.

### Adapter contract

```python
class MyPlatformAdapter(PlatformAdapter):
    name = "myplatform"
    display_name = "My Platform"
    kind = "live"

    def upload(self, asset_path):
        token = os.environ["MYPLATFORM_TOKEN"]  # from env, never hardcoded
        ...
        return UploadHandle(ref=media_url)

    def refetch(self, handle, dest_dir):
        ...
        return downloaded_path
```

## Ground rules

- **No secrets in commits.** Tokens come from the environment. `.env` is
  git-ignored; only `.env.example` (placeholders) is committed.
- **No real personal media in fixtures.** Everything in `tests/`, fixtures, and
  examples is synthetic and obviously fake.
- **Keep tests offline.** CI must pass with no network and no accounts. Use the
  mock adapter or recorded fixtures.
- **Run the suite before opening a PR:** `uv run pytest -q`.

## What this project deliberately does NOT do

It does **not** sign assets or re-attach stripped credentials. Re-attachment is
already solved by Adobe TrustMark and the CAI Soft-Binding Resolution API — this
tool *consumes and documents* them. See the README's "How this differs" section.
