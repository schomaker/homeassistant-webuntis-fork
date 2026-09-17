# WebUntis

### Custom component to access Web Untis data in Home Assistant

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
![Version](https://img.shields.io/github/v/release/schomaker/homeassistant-webuntis-fork)
[![Open Issues](https://img.shields.io/github/issues/schomaker/homeassistant-webuntis-fork?style=flat&label=Open%20Issues)](https://github.com/schomaker/homeassistant-webuntis-fork/issues)

---

## Features

| Feature | Description | Link |
|---------|-------------|------|
| **30-Day Calendar** | Displays all lessons in the calendar or calendar-card for the upcoming month. | [Entities & Services](docs/ENTITIES_AND_SERVICES.md) |
| **Lesson Sensors** | Includes school start/end times and next lesson, useful for wake-up automations. | [Examples & Automations](docs/EXAMPLES_AND_AUTOMATIONS.md) |
| **Lesson Change Notifications** | Get notified for cancellations, room changes, teacher changes, and lesson swaps. | [Notification Options](docs/OPTIONAL_CONFIGURATIONS.md#notification-options) |
| **Live Timetable (Live Activities)** | Display the current timetable in a live view on your phone or tablet. (Currently only available for iOS) | [Live Activities](docs/OPTIONAL_CONFIGURATIONS.md#live-activities) |
| **Fetch Lessons Service** | Request lessons for a specific date range. | [`webuntis.get_timetable`](docs/ENTITIES_AND_SERVICES.md#-webuntisget_timetable) |
| **Count Lessons Service** | Count lessons by subject within a given date range. | [`webuntis.count_lessons`](docs/ENTITIES_AND_SERVICES.md#-webuntiscount_lessons) |
| **Homework List & Dashboard Card** | Structured homework sensor plus a ready-made card that mirrors the WebUntis "Hausaufgaben" page, incl. print button. | [WebUntis Homework Card](docs/WEBUNTIS_HOMEWORK_CARD.md) |


---

## Setup
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=schomaker&repository=homeassistant-webuntis-fork)

You can install WebUntis via HACS or manually. For detailed instructions, see the dedicated setup guide:

[**Setup & Installation Guide**](docs/SETUP.md)


---

## 📖 Documentation

- **Entities & Services** – Full list of entities, their German/English names, and available services:
  [Entities & Services](docs/ENTITIES_AND_SERVICES.md)
- **Optional Configurations** – All configuration options for filters, calendars, lessons, notifications, live timetable, and backend:
  [Optional Configurations](docs/OPTIONAL_CONFIGURATIONS.md)
- **Examples & Automations** – Ready-to-use automations and template snippets for common use cases:
  [Examples & Automations](docs/EXAMPLES_AND_AUTOMATIONS.md)

---

## Dashboard Card for Timetable

For a better visual experience in Home Assistant, you can use the HA-Timetable-Card. It is designed to work with the timetable data provided by this integration and offers a more detailed and flexible way to display your timetable.

> [!NOTE]
> While this integration provides a calendar entitiy with the upcoming 30 days, the timetable card can request and display timetable data for a larger date range.

Check it out here: https://github.com/KingDando8430/HA-Timetable-Card

See the [WebUntis x Timetable Card Documentation](https://github.com/KingDando8430/HA-Timetable-Card/blob/main/documentation/WebUntis.md) for more information.

---

## Dashboard Card for Homework

A bundled custom Lovelace card renders the homework list grouped just like the WebUntis "Hausaufgaben"
page (Bald fällig / Noch nicht abgeschlossen / Verpasst), including a print button.

See [WebUntis Homework Card](docs/WEBUNTIS_HOMEWORK_CARD.md) for installation and configuration.

---

## Disclaimer
This project is not affiliated with WebUntis or Untis GmbH. All trademarks and logos belong to their respective owners. Use this integration at your own risk.
