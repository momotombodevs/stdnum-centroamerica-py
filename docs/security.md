# Security

## What the package does to protect itself

| Risk | Mitigation |
|------|------------|
| Denial of service with huge inputs | Inputs longer than 256 characters (`MAX_INPUT_LENGTH`) are `FORMAT` errors; no regular expression runs. |
| Regular expressions with catastrophic backtracking (ReDoS) | Linear patterns with no nested quantifiers, always used with `fullmatch`. The tests time them against adversarial inputs. |
| Unicode tricks | Only ASCII text is accepted. Arabic-Indic and full-width digits (which `int()` and `str.isdigit()` accept), Unicode hyphens, invisible spaces and letters that change when upper-cased (`ß` → `SS`) are rejected. |
| `$` matching before a trailing newline | `fullmatch` is used instead of `^...$`. |
| Unexpected types | Anything other than `str` raises `TypeError`; nothing is silently converted. |
| Shared state | Instances and data tables are immutable; `register()` uses a lock. |
| Leaking personal data | The package logs nothing; exceptions never include the number; `repr()` of parsed components hides dates, names and sequence numbers. |
| Supply chain | No dependencies; releases published from GitHub Actions with Trusted Publishing and attestations; actions pinned by commit SHA. |

## Recommendations for integrators

1. **A document number is personal data**, even when it is valid. Encrypt it at rest if the law that applies to you requires it, restrict who can read it and keep it out of logs.
2. **Framework validation errors include the input**, for example the `input` field of FastAPI 422 responses. Strip it before logging validation errors.
3. **Validation is not identity verification.** A valid number only has the right shape and check digit; it does not prove that it exists or belongs to whoever sent it. That requires checking with the issuing institution.
4. **Do not decide legal age from a Nicaraguan cédula**: `birth_year_candidates()` can return both 1910 and 2010 for the same number.
5. **`generate()` is for tests.** The numbers are random and may match those of real people: do not use them as production data or publish them as examples of people.
6. **Pin the version and install with hashes** in production (see [installation.md](installation.md)).
7. **Limit request size** in your web server or framework. The package rejects a huge input quickly, but by then the server has already read it into memory.

## Reporting a vulnerability

See [SECURITY.md](../SECURITY.md).
