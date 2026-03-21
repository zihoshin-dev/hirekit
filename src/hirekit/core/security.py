"""Security utilities — SSRF prevention, input sanitization."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# SSRF prevention
# ---------------------------------------------------------------------------

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # RFC1918
    ipaddress.ip_network("172.16.0.0/12"),     # RFC1918
    ipaddress.ip_network("192.168.0.0/16"),    # RFC1918
    ipaddress.ip_network("169.254.0.0/16"),    # link-local
    ipaddress.ip_network("100.64.0.0/10"),     # shared address space
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]


def validate_url(url: str) -> str:
    """Validate a URL is safe to fetch (blocks SSRF targets).

    Returns the URL unchanged if safe.
    Raises ValueError if the URL targets an internal/private address.
    """
    if not url:
        raise ValueError("URL must not be empty")

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Disallowed URL scheme: {parsed.scheme!r}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")

    # Reject raw IP addresses pointing to private/loopback ranges
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                raise ValueError(
                    f"Request to private/internal address is not allowed: {hostname}"
                )
    except ValueError as exc:
        # ip_address() raises ValueError for non-IP hostnames — re-raise only
        # our own SSRF errors (they contain the word "allowed")
        if "allowed" in str(exc):
            raise

    # Block reserved hostnames that always map to localhost
    _blocked = {"localhost", "localhost.localdomain"}
    if hostname.lower() in _blocked:
        raise ValueError(
            f"Request to reserved hostname is not allowed: {hostname}"
        )

    return url


# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------

_PATH_TRAVERSAL_RE = re.compile(r"[/\\]|\.\.")


def sanitize_company_name(name: str) -> str:
    """Remove path-traversal characters from a company name.

    Strips leading/trailing whitespace and removes ``..``, ``/``, and ``\\``.
    """
    if not name:
        return name
    sanitized = _PATH_TRAVERSAL_RE.sub("", name)
    return sanitized.strip()


def sanitize_region(region: str) -> str:
    """Allow only alphanumeric region codes (e.g., 'kr', 'us', 'global').

    Raises ValueError if the value contains unexpected characters.
    """
    if not re.match(r"^[a-zA-Z0-9_-]{1,16}$", region):
        raise ValueError(f"Invalid region value: {region!r}")
    return region
