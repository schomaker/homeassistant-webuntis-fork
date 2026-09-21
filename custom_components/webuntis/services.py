"""Services for WebUntis integration."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.service import async_extract_config_entry_ids

from .const import DOMAIN
from .utils.homework import format_homework_text
from .utils.ipp_print import async_print_text, resolve_ipp_uri

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for WebUntis integration."""

    if not hass.services.has_service(DOMAIN, "print_homework"):

        async def async_handle_print_homework(call: ServiceCall) -> None:
            """Render a homework-list sensor's data as text and send it to an IPP printer."""
            entity_id = call.data["entity_id"]
            printer_uri = call.data.get("printer_uri")
            printer_entity_id = call.data.get("printer_entity_id")

            if not printer_uri:
                if not printer_entity_id:
                    raise HomeAssistantError(
                        "Either printer_entity_id or printer_uri is required"
                    )
                printer_state = hass.states.get(printer_entity_id)
                if printer_state is None:
                    raise HomeAssistantError(
                        f"Entity {printer_entity_id} not found"
                    )
                uri_supported = printer_state.attributes.get("uri_supported")
                if not uri_supported:
                    raise HomeAssistantError(
                        f"{printer_entity_id} has no 'uri_supported' attribute "
                        "(expected the Home Assistant IPP integration's printer "
                        "status sensor)"
                    )
                printer_uri = resolve_ipp_uri(uri_supported)

            sensor_state = hass.states.get(entity_id)
            if sensor_state is None:
                raise HomeAssistantError(f"Entity {entity_id} not found")

            homeworks = sensor_state.attributes.get("homeworks", [])
            title = call.data.get("title", "Hausaufgaben")
            text = format_homework_text(homeworks, title=title)

            try:
                await async_print_text(hass, printer_uri, text, job_name=title)
            except Exception as error:  # noqa: BLE001
                raise HomeAssistantError(f"Printing failed: {error}") from error

        hass.services.async_register(
            DOMAIN, "print_homework", async_handle_print_homework
        )

    if hass.services.has_service(DOMAIN, "get_timetable"):
        return

    async def async_call_webuntis_service(service_call: ServiceCall) -> None:
        """Call correct WebUntis service."""

        entry_id = await async_extract_config_entry_ids(service_call)
        config_entry = hass.config_entries.async_get_entry(list(entry_id)[0])
        webuntis_object = hass.data[DOMAIN][config_entry.unique_id]

        data = service_call.data

        if "start" in data and "end" in data:
            start_date = datetime.strptime(data["start"], "%Y-%m-%d")
            end_date = datetime.strptime(data["end"], "%Y-%m-%d")

            if end_date < start_date:
                raise HomeAssistantError(f"Start date has to be before end date")

        await hass.async_add_executor_job(webuntis_object.webuntis_login)

        result = None

        if service_call.service == "get_timetable":
            lesson_list = await hass.async_add_executor_job(
                webuntis_object._get_events_in_timerange,
                start_date,
                end_date,
                data["apply_filter"],
                data["show_cancelled"],
                data["compact_result"],
                data.get("compact_tolerance_minutes", 0),
            )
            result = {"lessons": lesson_list}

        elif service_call.service == "count_lessons":
            result = await hass.async_add_executor_job(
                webuntis_object._count_lessons,
                start_date,
                end_date,
                data["apply_filter"],
                data["count_cancelled"],
            )

        elif service_call.service == "get_schoolyears":
            result = await hass.async_add_executor_job(webuntis_object._get_schoolyears)

        await hass.async_add_executor_job(webuntis_object.webuntis_logout)

        return result

    hass.services.async_register(
        DOMAIN,
        "get_timetable",
        async_call_webuntis_service,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "count_lessons",
        async_call_webuntis_service,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        "get_schoolyears",
        async_call_webuntis_service,
        supports_response=SupportsResponse.ONLY,
    )
