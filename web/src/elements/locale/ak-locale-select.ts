import { formatLocaleOptions, PseudoLocale, TargetLocale } from "#common/ui/locale/definitions";
import { setSessionLocale } from "#common/ui/locale/utils";

import { AKElement } from "#elements/Base";
import Styles from "#elements/locale/ak-locale-select.css";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLocale } from "#elements/mixins/locale";

import { CapabilitiesEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import { repeat } from "lit/directives/repeat.js";

@customElement("ak-locale-select")
export class AKLocaleSelect extends WithLocale(WithCapabilitiesConfig(AKElement)) {
    public static shadowRootOptions = {
        ...AKElement.shadowRootOptions,
        delegatesFocus: true,
    };

    public static readonly styles = [Styles];

    //#region Listeners

    #localeChangeListener = (event: Event) => {
        const select = event.target as HTMLSelectElement;
        const locale = select.value as TargetLocale;

        this.locale = locale;

        setSessionLocale(locale);
        this.blur();
    };

    #selectRef = createRef<HTMLSelectElement>();

    /**
     * Show the locale select dropdown.
     */
    public show = () => {
        const selectElement = this.#selectRef.value;

        if (!selectElement) {
            return;
        }

        // Gracefully degrade if not supported.
        try {
            selectElement.showPicker();
        } catch (_error) {
            selectElement.focus();
        }
    };

    //#endregion

    //#region Lifecycle

    public override connectedCallback(): void {
        super.connectedCallback();

        this.addEventListener("click", this.show);
    }

    //#endregion

    protected override render() {
        const { locale } = this;
        let localeOptions = formatLocaleOptions();

        if (!this.can(CapabilitiesEnum.CanDebug)) {
            localeOptions = localeOptions.filter(([, code]) => code !== PseudoLocale);
        }

        const options = repeat(
            localeOptions,
            ([_locale, code]) => code,
            ([label, code]) =>
                html`<option value=${code} ?selected=${code === locale}>${label}</option>`,
        );

        return html`<label
                part="label"
                for="locale-selector"
                @click=${this.show}
                aria-label=${msg("Select language", {
                    id: "language-selector-label",
                    desc: "Label for the language selection dropdown",
                })}
            >
                <svg
                    class="icon"
                    role="img"
                    aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 32 32"
                >
                    <path
                        d="M27.85 29H30l-6-15h-2.35l-6 15h2.15l1.6-4h6.85Zm-7.65-6 2.62-6.56L25.45 23ZM18 7V5h-7V2H9v3H2v2h10.74a14.7 14.7 0 0 1-3.19 6.18A13.5 13.5 0 0 1 7.26 9h-2.1a16.5 16.5 0 0 0 3 5.58A16.8 16.8 0 0 1 3 18l.75 1.86A18.5 18.5 0 0 0 9.53 16a16.9 16.9 0 0 0 5.76 3.84L16 18a14.5 14.5 0 0 1-5.12-3.37A17.64 17.64 0 0 0 14.8 7Z"
                    />
                </svg>
            </label>
            <select
                ${ref(this.#selectRef)}
                part="select"
                id="locale-selector"
                @change=${this.#localeChangeListener}
                class="pf-c-form-control"
                name="locale"
            >
                ${options}
            </select>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-locale-select": AKLocaleSelect;
    }
}
