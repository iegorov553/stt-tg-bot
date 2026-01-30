# Security Policy

## Reporting

Please report security issues privately to the maintainers.

## Known Vulnerabilities

The current `aiogram` dependency requires `aiohttp < 3.13`, but `pip-audit` reports
multiple CVEs fixed in `aiohttp 3.13.3`. Until `aiogram` allows `aiohttp >= 3.13.3`,
the following CVEs are temporarily ignored in `pip-audit` runs:

- CVE-2025-69223
- CVE-2025-69224
- CVE-2025-69225
- CVE-2025-69226
- CVE-2025-69227
- CVE-2025-69228
- CVE-2025-69229
- CVE-2025-69230

Mitigation: monitor `aiogram` updates and upgrade `aiohttp` as soon as a compatible
release is available. Replace the ignore list with the upgraded version.
