"""RTSP URL helpers."""

from __future__ import annotations

from urllib.parse import quote, urlsplit, urlunsplit

from analytics_vms.inventory import InventoryRow


class RtspUrlError(ValueError):
    """Raised when an RTSP URL cannot be built safely."""


def build_rtsp_url(row: InventoryRow) -> str:
    """Build an RTSP URL from a normalized inventory row."""
    path = _normalize_rtsp_path(row.rtsp_path)
    host = row.ip.strip()

    if not host:
        raise RtspUrlError("No se puede construir URL RTSP sin host/IP.")

    if row.rtsp_port < 1 or row.rtsp_port > 65535:
        raise RtspUrlError("No se puede construir URL RTSP con puerto fuera de rango.")

    username = row.username.strip()
    password = row.password.strip()
    if bool(username) != bool(password):
        raise RtspUrlError(
            "No se puede construir URL RTSP con credenciales incompletas."
        )

    authority = f"{host}:{row.rtsp_port}"
    if username and password:
        quoted_username = quote(username, safe="")
        quoted_password = quote(password, safe="")
        authority = f"{quoted_username}:{quoted_password}@{authority}"

    return f"rtsp://{authority}{path}"


def mask_rtsp_url(url: str) -> str:
    """Return an RTSP URL with password credentials masked."""
    parts = urlsplit(url)
    if "@" not in parts.netloc:
        return url

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    if ":" not in userinfo:
        return url

    username, _password = userinfo.rsplit(":", 1)
    masked_netloc = f"{username}:***@{hostinfo}"
    return urlunsplit(
        (parts.scheme, masked_netloc, parts.path, parts.query, parts.fragment)
    )


def _normalize_rtsp_path(path: str) -> str:
    """Normalize an RTSP path without escaping path separators."""
    normalized = path.strip()
    if not normalized:
        raise RtspUrlError("No se puede construir URL RTSP sin rtsp_path.")
    if normalized.startswith("/"):
        return normalized
    return f"/{normalized}"
