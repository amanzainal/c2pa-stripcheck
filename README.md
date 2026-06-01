# c2pa-stripcheck

**Does platform X strip your Content Credentials?**

An automated tester and crowd-maintained matrix for whether platforms strip
[C2PA](https://c2pa.org/) Content Credentials on upload.

> A status badge can be generated from `matrix/badge.json` (a
> [shields.io endpoint](https://shields.io/badges/endpoint-badge) JSON produced
> from the matrix).

---

## The problem

You sign an image with Content Credentials (C2PA), upload it to a social
platform, and... does the provenance survive? Today the only answers are
**scattered manual blog anecdotes** — "I tried it in March and it stripped
everything." There is no automated, repeatable, *versioned* record of what each
platform actually does.

The verified gap: **re-attachment is already solved** — Adobe
[TrustMark](https://github.com/adobe/trustmark) (a soft-binding watermark) plus
the [CAI Soft-Binding Resolution API](https://opensource.contentauthenticity.org/)
let you recover provenance even after the embedded manifest is removed. So this
tool does **not** rebuild signing or re-attachment. What nobody packages is the
**measurement loop**: upload a signed asset → re-fetch the platform's processed
copy → classify what happened → aggregate into a versioned matrix.

That measurement loop, and the crowd-maintained matrix it produces, is the whole
point of this project.

## What it does

For each platform, it runs a **probe**:

1. **Upload** a signed asset to the platform.
2. **Re-fetch** the platform's processed copy.
3. **Read** the Content Credentials before and after (via `c2pa-python`,
   `c2patool`, or a built-in structural scanner — whichever is available).
4. **Classify** the outcome as one of four verdicts:

   | Verdict | Meaning |
   |---|---|
   | ✅ **PRESERVED** | Manifest survived intact (same signer). |
   | ❌ **STRIPPED** | Manifest gone, nothing recoverable. |
   | 🔁 **RE-SIGNED** | Manifest replaced by the platform's own credentials. |
   | 🔗 **SOFT-BINDING-RECOVERABLE** | Embedded manifest gone, but a TrustMark watermark survives → provenance recoverable via the CAI Soft-Binding Resolution API. |

5. **Aggregate** all probes into a versioned **Markdown + JSON matrix** and a
   status **badge**.

## How this differs from existing tools

This deliberately does **not** re-implement what already exists:

| Tool | What it does | What it does *not* do |
|---|---|---|
| [`c2patool`](https://github.com/contentauth/c2patool) / [`c2pa-python`](https://github.com/contentauth/c2pa-python) | Read / verify / **sign** a single asset's manifest | No upload→re-fetch loop, no cross-platform matrix |
| [`c2pie`](https://pypi.org/project/c2pie/) / [`c2pa-rs`](https://github.com/contentauth/c2pa-rs) | **Construct & sign** C2PA manifests | Not a strip-tester |
| [Adobe TrustMark](https://github.com/adobe/trustmark) + [CAI Soft-Binding Resolution API](https://opensource.contentauthenticity.org/) | **Re-attach / recover** provenance after stripping | Not a tester; this tool *consumes* them |
| [`contentauth/c2pa-attacks`](https://github.com/contentauth/c2pa-attacks) | Security / fuzzing of manifests | Not about platform strip behavior |
| [Content Credentials Verify site](https://contentcredentials.org/verify) / viewers | Inspect one asset in a browser | Manual, single-asset, not a versioned matrix |

`c2pa-stripcheck` is the only one that packages the **upload → re-fetch →
classify → versioned matrix** workflow, and treats the matrix as a
**crowd-maintained** artifact.

## Install

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/AmanZainal/c2pa-stripcheck
cd c2pa-stripcheck
uv sync
```

Optional, for cryptographic verification of real assets:

```bash
uv sync --extra verify          # installs c2pa-python
# or install the c2patool CLI from contentauth/c2pa-rs and put it on PATH
```

The tool degrades gracefully: with neither installed it uses a built-in
structural scanner (enough to drive the demo and detect manifest presence).

## Usage

### Demo (fully offline — no accounts, no network, no GPU)

```bash
uv run c2pa-stripcheck run --demo --out runs/demo
```

Sample output:

```
              C2PA Content Credentials — Platform Behavior Matrix
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Platform               ┃ Verdict                     ┃ Reader          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Preserve Co (demo)     │ ✅ PRESERVED                │ builtin-scanner │
│ StripNet (demo)        │ ❌ STRIPPED                 │ builtin-scanner │
│ ReSignApp (demo)       │ 🔁 RE-SIGNED                │ builtin-scanner │
│ SoftBind Social (demo) │ 🔗 SOFT-BINDING-RECOVERABLE │ builtin-scanner │
└────────────────────────┴─────────────────────────────┴─────────────────┘

Wrote runs/demo/matrix.json
Wrote runs/demo/MATRIX.md
Wrote runs/demo/badge.json
```

The demo uses **synthetic, obviously-fake** assets and a mock platform adapter,
so it exercises the full verify → classify → matrix → report pipeline with no
external dependencies.

### Other commands

```bash
uv run c2pa-stripcheck list          # known platform adapters + status
uv run c2pa-stripcheck readers       # which manifest readers are available
uv run c2pa-stripcheck matrix runs/demo/matrix.json --out runs/rerender
```

### Real platform probe (needs accounts)

```bash
cp .env.example .env                 # fill in real tokens
uv run c2pa-stripcheck run --platform instagram --asset my-signed.jpg --out runs/ig
```

Real adapters are **stubs** in v0 — they document the upload/re-fetch path and
the required credentials, but raise until a contributor wires them up (or you
record observed behavior by hand). See [CONTRIBUTING.md](CONTRIBUTING.md). A stub
probe yields an honest `UNTESTED` verdict, never a fake result.

## Real vs. demo: what needs what

| Capability | Demo | Real run |
|---|---|---|
| Verify / classify / matrix / report logic | ✅ offline | ✅ |
| Synthetic fixtures + mock adapter | ✅ | — |
| Cryptographic manifest validation | structural only | needs `c2pa-python` or `c2patool` |
| Live upload to a platform | — | needs an account + token + a working adapter |
| Soft-binding recovery via CAI API | simulated | needs network + the CAI endpoint |

No GPU is needed for anything. The demo and the **entire test suite** run with no
network and no accounts.

## The matrix is the point

The committed [`matrix/`](matrix/) directory is the canonical, versioned record.
It ships seeded with every known platform marked `UNTESTED`. As contributors run
real probes or record observations, the matrix fills in — that crowd-maintained
record is the community value here, not any single live adapter.

## Roadmap

- [ ] Implement the first real adapter (likely Reddit or X) end-to-end.
- [ ] Wire the CAI Soft-Binding Resolution API for real recovery checks.
- [ ] Per-format rows (JPEG vs PNG vs MP4 often differ on the same platform).
- [ ] GitHub Action that regenerates the badge from `matrix/matrix.json`.
- [ ] History view: track when a platform's behavior changes over time.
- [ ] Optional HTML matrix output.

## Development

```bash
uv run pytest -q                                        # run the test suite
uv run --with pytest-cov pytest --cov=c2pa_stripcheck   # with coverage
```

## License

MIT © Aman Zainal. See [LICENSE](LICENSE).
