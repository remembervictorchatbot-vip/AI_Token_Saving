# Security Policy

## Supported versions

Only the latest commit on `main` is supported. Releases are tagged when they
happen; the latest tag is the current supported release.

## Reporting a vulnerability

**Please do NOT open a public issue for security problems.**

Report privately instead, either:

- GitHub **Security Advisory**: repo → Security → "Report a vulnerability", or
- contact the maintainer through the email/contact shown on the GitHub profile.

Include in the report:

1. Affected file / command / surface (e.g. `toks`, `crl`, a skill's scripts).
2. Impact and severity as you understand it.
3. A minimal reproduction (no real secrets — this project is designed to never
   read credentials, but follow safe handling anyway).

We aim to acknowledge reports within 48 hours and to coordinate a fix before
public disclosure. Thank you for keeping this project safe.

## Scope

This repository is a set of skills and a pure-stdlib Python toolkit. It has no
third-party runtime dependencies, does not collect telemetry, and does not read
credentials. Most "vulnerabilities" here are instruction-level (a skill telling
the agent to do something unsafe) — treat skill content with the same scrutiny
as code.
