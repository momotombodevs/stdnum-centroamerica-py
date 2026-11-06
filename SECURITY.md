# Security Policy

This package only validates the format and check digits of document numbers: it makes no network requests and stores no data. The following are still treated as security issues:

- an input that causes a denial of service (for example, a regular expression with catastrophic backtracking or disproportionate memory use);
- validation that systematically accepts numbers it should reject (for example, through Unicode characters);
- any path through which the package exposes the numbers it receives (logs, error messages, `repr()`).

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/momotombodevs/stdnum-centroamerica-py/security/advisories/new). Please do not open a public issue with the details.

You will receive an acknowledgement within a few days and updates until a fix is released.

## Supported versions

Only the latest published minor version.

## Verifying a published release

Every release is published from GitHub Actions with Trusted Publishing and attestations (PEP 740). The package page on PyPI shows that each file comes from this repository and the `release.yml` workflow.
