"""Minimal IPP (Internet Printing Protocol) client for a single Print-Job.

Implements just enough of RFC 8010 to submit a one-shot "Print-Job"
operation with the document embedded in the same request. This avoids
depending on an external IPP client library that isn't published on
PyPI (only status/monitoring clients like the pyipp package used by
Home Assistant's core IPP integration are). The binary layout has been
stable for decades, so a small hand-rolled encoder is a reasonable
trade-off here.
"""

from __future__ import annotations

import struct

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_IPP_VERSION = b"\x01\x01"  # IPP/1.1
_OP_PRINT_JOB = b"\x00\x02"
_TAG_OPERATION_ATTRIBUTES = b"\x01"
_TAG_END_OF_ATTRIBUTES = b"\x03"

_TAG_URI = 0x45
_TAG_NAME_WITHOUT_LANGUAGE = 0x42
_TAG_CHARSET = 0x47
_TAG_NATURAL_LANGUAGE = 0x48
_TAG_MIME_MEDIA_TYPE = 0x49

_SUCCESSFUL_STATUS_MAX = 0x00FF


def _encode_attribute(value_tag: int, name: str, value: str) -> bytes:
    """Encode a single-value IPP attribute (RFC 8010 section 3.5.2)."""
    name_bytes = name.encode("us-ascii")
    value_bytes = value.encode("utf-8")
    return (
        bytes([value_tag])
        + struct.pack(">H", len(name_bytes))
        + name_bytes
        + struct.pack(">H", len(value_bytes))
        + value_bytes
    )


def _build_print_job_request(
    printer_uri: str, job_name: str, user_name: str, document_format: str
) -> bytes:
    request_id = struct.pack(">I", 1)
    operation_attributes = b"".join(
        [
            _encode_attribute(_TAG_CHARSET, "attributes-charset", "utf-8"),
            _encode_attribute(
                _TAG_NATURAL_LANGUAGE, "attributes-natural-language", "de"
            ),
            _encode_attribute(_TAG_URI, "printer-uri", printer_uri),
            _encode_attribute(
                _TAG_NAME_WITHOUT_LANGUAGE, "requesting-user-name", user_name
            ),
            _encode_attribute(_TAG_NAME_WITHOUT_LANGUAGE, "job-name", job_name),
            _encode_attribute(
                _TAG_MIME_MEDIA_TYPE, "document-format", document_format
            ),
        ]
    )
    return (
        _IPP_VERSION
        + _OP_PRINT_JOB
        + request_id
        + _TAG_OPERATION_ATTRIBUTES
        + operation_attributes
        + _TAG_END_OF_ATTRIBUTES
    )


def resolve_ipp_uri(uri_supported: str) -> str:
    """Pick a usable IPP URI from an IPP printer's comma-separated uri-supported value.

    Prefers plain "ipp://" over "ipps://" since a home-network printer's
    TLS certificate usually can't be validated.
    """
    uris = [u.strip() for u in str(uri_supported).split(",") if u.strip()]
    if not uris:
        raise ValueError("uri_supported is empty")
    for uri in uris:
        if uri.startswith("ipp://"):
            return uri
    return uris[0]


def _ipp_uri_to_http(printer_uri: str) -> str:
    """Map an ipp:// / ipps:// URI to the equivalent http(s):// URL.

    IPP is transported over HTTP; only the URI scheme differs.
    """
    if printer_uri.startswith("ipps://"):
        return "https://" + printer_uri[len("ipps://") :]
    if printer_uri.startswith("ipp://"):
        return "http://" + printer_uri[len("ipp://") :]
    return printer_uri


async def async_print_text(
    hass: HomeAssistant,
    printer_uri: str,
    text: str,
    job_name: str = "Home Assistant",
    user_name: str = "home-assistant",
) -> None:
    """Submit a plain-text document as an IPP Print-Job.

    Raises RuntimeError when the printer's IPP response reports a
    non-successful status code, or when the HTTP request itself fails.
    """
    request = _build_print_job_request(
        printer_uri, job_name, user_name, "text/plain"
    )
    body = request + text.encode("utf-8")

    session = async_get_clientsession(hass)
    url = _ipp_uri_to_http(printer_uri)

    async with session.post(
        url,
        data=body,
        headers={"Content-Type": "application/ipp"},
    ) as response:
        response.raise_for_status()
        response_body = await response.read()

    if len(response_body) < 4:
        raise RuntimeError("Empty or invalid IPP response from printer")

    status_code = struct.unpack(">H", response_body[2:4])[0]
    if status_code > _SUCCESSFUL_STATUS_MAX:
        raise RuntimeError(
            f"Printer rejected the print job (IPP status 0x{status_code:04x})"
        )
