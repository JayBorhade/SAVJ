# Security Policy

## Reporting a vulnerability

Please do not publish exploitable vulnerabilities, credentials, personal data, or proof images in public issues.

Report suspected security issues privately to the repository owner through GitHub's private vulnerability reporting feature, if enabled. Include the affected commit/branch, impact, minimal reproduction steps, and any relevant logs with secrets and personal information removed.

## Supported security expectations

- Never commit production credentials, access tokens, private keys, or real user data.
- Keep authorization and validation on the server; client-side checks are UX only.
- Treat uploaded files and all user-controlled input as untrusted.
- Do not claim production readiness until the security release gates in `docs/SECURITY_AUDIT.md` are verified against the deployed configuration.
- Rotate any credential suspected to have been exposed; deleting it from the latest commit is not sufficient.
