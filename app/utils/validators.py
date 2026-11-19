import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")
BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "metadata"}


class UrlValidationError(ValueError):
    pass


class UnsafeUrlError(ValueError):
    pass


def _is_blocked_ip(address):
    ip = ipaddress.ip_address(address.split("%")[0])
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _resolve_host(hostname):
    try:
        return socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UrlValidationError("Could not resolve hostname: " + hostname) from exc


async def validate_public_url(raw_url):
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise UrlValidationError("URL is required")

    candidate = raw_url.strip()
    if " " in candidate or "\n" in candidate or "\t" in candidate:
        raise UrlValidationError("URL contains invalid whitespace")
    if not candidate.lower().startswith(("http://", "https://")):
        raise UrlValidationError("URL must start with http:// or https://")

    parts = urlsplit(candidate)
    if not parts.hostname or parts.username or parts.password:
        raise UrlValidationError("URL must contain a hostname and no credentials")
    try:
        port = parts.port
    except ValueError as exc:
        raise UrlValidationError("URL contains an invalid port") from exc
    if port not in (None, 80, 443):
        raise UrlValidationError("Only standard HTTP and HTTPS ports are allowed")

    hostname = parts.hostname.lower().rstrip(".")
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_SUFFIXES):
        raise UnsafeUrlError("Private or internal hostnames are not allowed")
    if hostname.replace(".", "").isdigit():
        raise UnsafeUrlError("Numeric host addresses are not allowed")

    resolved = await asyncio.to_thread(_resolve_host, hostname)
    addresses = {entry[4][0] for entry in resolved}
    if not addresses:
        raise UrlValidationError("Could not resolve hostname: " + hostname)
    if any(_is_blocked_ip(address) for address in addresses):
        raise UnsafeUrlError("Private, loopback, link-local or reserved addresses are not allowed")

    scheme = parts.scheme.lower()
    default_port = 443 if scheme == "https" else 80
    port = parts.port or default_port
    netloc = hostname if port == default_port else hostname + ":" + str(port)
    path = parts.path or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


async def validate_redirect_url(url):
    return await validate_public_url(url)
