"""Services for WebUntis integration."""

from __future__ import annotations

import base64
import logging
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.service import async_extract_config_entry_ids

from .const import DOMAIN
from .utils.ipp_render import render_homework_jpeg

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for WebUntis integration."""

    if not hass.services.has_service(DOMAIN, "print_homework"):

        async def async_handle_print_homework(call: ServiceCall) -> None:
            """Render a homework-list sensor's data as a JPEG and print it via ipp_printing.

            Delegates the actual IPP transport to the ipp_printing integration
            (ipp_printing.print) instead of talking IPP directly: this printer
            only advertises PCLXL/PostScript/PCL5E/PJL document formats over
            IPP, not text/plain, so image/jpeg is what actually works.
            """
            if not hass.services.has_service("ipp_printing", "print"):
                raise HomeAssistantError(
                    "The 'ipp_printing' integration is required for "
                    "webuntis.print_homework but isn't installed"
                )

            entity_id = call.data["entity_id"]
            printer_entity_id = call.data["printer_entity_id"]

            sensor_state = hass.states.get(entity_id)
            if sensor_state is None:
                raise HomeAssistantError(f"Entity {entity_id} not found")

            homeworks = sensor_state.attributes.get("homeworks", [])
            title = call.data.get("title", "Hausaufgaben")

            jpeg_bytes = await hass.async_add_executor_job(
                render_homework_jpeg, homeworks, title
            )

            try:
                await hass.services.async_call(
                    "ipp_printing",
                    "print",
                    {
                        "data": base64.b64encode(jpeg_bytes).decode("ascii"),
                        "mimetype": "image/jpeg",
                        "paper_size": "iso_a4_210x297mm",
                    },
                    target={"entity_id": printer_entity_id},
                    blocking=True,
                )
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
