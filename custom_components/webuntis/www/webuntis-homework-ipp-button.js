/**
 * WebUntis Homework IPP Print Button
 *
 * A button card that sends the current homework list straight to a
 * network printer via IPP (no browser print dialog).
 *
 * type: custom:webuntis-homework-ipp-button
 * entity: sensor.<name>_homework_list        # required
 * printer: sensor.some_ipp_printer_status    # required - an entity from the
 *                                             # "ipp" integration, as targeted
 *                                             # by ipp_printing.print
 * title: "Hausaufgaben drucken"              # optional, button label
 * print_title: "Hausaufgaben"                # optional, document title / print job name
 *
 * Requires the "ipp_printing" integration (provides ipp_printing.print,
 * which webuntis.print_homework delegates the actual IPP transport to).
 */

class WebuntisHomeworkIppButton extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("Bitte eine 'entity' angeben (sensor.<name>_homework_list)");
    }
    if (!config.printer) {
      throw new Error("Bitte 'printer' angeben (Entity der 'ipp'-Integration)");
    }
    this._config = config;

    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    this._built = false;
    this._busy = false;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 1;
  }

  _label() {
    const lang = (this._hass && this._hass.language) || "de";
    if (this._config.title) return this._config.title;
    return lang.startsWith("de") ? "Hausaufgaben drucken" : "Print homework";
  }

  _notify(message) {
    this.dispatchEvent(
      new CustomEvent("hass-notification", {
        bubbles: true,
        composed: true,
        detail: { message },
      })
    );
  }

  async _print() {
    if (this._busy) return;
    this._busy = true;
    this._render();

    const lang = (this._hass && this._hass.language) || "de";
    const data = {
      entity_id: this._config.entity,
      printer_entity_id: this._config.printer,
      title: this._config.print_title || "Hausaufgaben",
    };

    try {
      await this._hass.callService("webuntis", "print_homework", data);
      this._notify(lang.startsWith("de") ? "Druckauftrag gesendet." : "Print job sent.");
    } catch (err) {
      const message = (err && err.message) || String(err);
      this._notify(
        (lang.startsWith("de") ? "Drucken fehlgeschlagen: " : "Printing failed: ") + message
      );
    } finally {
      this._busy = false;
      this._render();
    }
  }

  _render() {
    if (!this._hass || !this._config) return;

    if (!this._built) {
      this.shadowRoot.innerHTML = `
        <style>
          ha-card { padding: 0; }
          ha-card:not(:defined) { display: block; border-radius: 12px; background: var(--card-background-color, #fff);
            box-shadow: 0 2px 4px rgba(0,0,0,0.14), 0 2px 2px rgba(0,0,0,0.12); }
          button.print-btn { width: 100%; display: flex; align-items: center; justify-content: center;
            gap: 8px; padding: 16px; background: none; border: none; cursor: pointer;
            color: var(--primary-color); font-size: 1em; font-family: inherit; }
          button.print-btn:disabled { opacity: 0.5; cursor: default; }
          button.print-btn:hover:not(:disabled) { background: var(--secondary-background-color); }
          svg { fill: currentColor; width: 22px; height: 22px; }
        </style>
        <ha-card>
          <button class="print-btn">
            <svg viewBox="0 0 24 24"><path d="M19,8H5A3,3 0 0,0 2,11V17H6V21H18V17H22V11A3,3 0 0,0 19,8M16,19H8V14H16V19M19,12A1,1 0 0,1 18,11A1,1 0 0,1 19,10A1,1 0 0,1 20,11A1,1 0 0,1 19,12M18,3H6V7H18V3Z" /></svg>
            <span class="label"></span>
          </button>
        </ha-card>
      `;
      this.shadowRoot
        .querySelector(".print-btn")
        .addEventListener("click", () => this._print());
      this._built = true;
    }

    const button = this.shadowRoot.querySelector(".print-btn");
    button.disabled = this._busy;
    this.shadowRoot.querySelector(".label").textContent = this._busy
      ? ((this._hass.language || "de").startsWith("de") ? "Druckt..." : "Printing...")
      : this._label();
  }
}

customElements.define("webuntis-homework-ipp-button", WebuntisHomeworkIppButton);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "webuntis-homework-ipp-button",
  name: "WebUntis Homework Print Button",
  description: "Druckt die WebUntis-Hausaufgabenliste direkt per IPP auf einem Netzwerkdrucker.",
});
