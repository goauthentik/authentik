import { localized, msg } from "@lit/localize";
import { LitElement, html } from "lit";
import { customElement } from "lit/decorators.js";

import "./ak-locale-context";
import { EVENT_LOCALE_REQUEST, LocaleContextEventDetail } from "./events.js";

export default {
    title: "Elements / Shell / Locale Context",
};

@localized()
@customElement("ak-locale-demo-component")
export class AKLocaleDemoComponent extends LitElement {
    render() {
        return html`<span>${msg("Everything is ok.")}</span>`;
    }
}

@localized()
@customElement("ak-locale-sensitive-demo-component")
export class AKLocaleSensitiveDemoComponent extends LitElement {
    render() {
        return html`<p>${msg("Everything is ok.")}</p>`;
    }
}

export const InFrench = () =>
    html`<div style="background: #fff; padding: 4em">
        <ak-locale-context locale="fr"
            ><ak-locale-demo-component
                >Everything is not ok.</ak-locale-demo-component
            ></ak-locale-context
        >
    </div>`;

export const SwitchingBackAndForth = () => {
    let languageCode = "en";

    window.setInterval(() => {
        languageCode = languageCode === "en" ? "fr" : "en";

        window.dispatchEvent(
            new CustomEvent<LocaleContextEventDetail>(EVENT_LOCALE_REQUEST, {
                composed: true,
                bubbles: true,
                detail: { locale: languageCode },
            }),
        );
    }, 1000);

    return html`<div style="background: #fff; padding: 4em">
        <ak-locale-context locale="fr">
            <ak-locale-sensitive-demo-component></ak-locale-sensitive-demo-component
        ></ak-locale-context>
    </div>`;
};
