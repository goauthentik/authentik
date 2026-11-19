import { TargetLanguageTag } from "#common/ui/locale/definitions";
import { formatLocaleDisplayNames } from "#common/ui/locale/format";
import { applyLocaleChange } from "#common/ui/locale/persist";

import { AKElement } from "#elements/Base";
import Styles from "#elements/locale/ak-locale-select.css";
import { LocaleOptions } from "#elements/locale/utils";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLocale } from "#elements/mixins/locale";

import { CapabilitiesEnum } from "@goauthentik/api";

import { guard } from "lit-html/directives/guard.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-locale-select")
export class AKLocaleSelect extends WithLocale(WithCapabilitiesConfig(AKElement)) {
    public static shadowRootOptions = {
        ...AKElement.shadowRootOptions,
        delegatesFocus: true,
    };

    public static readonly styles = [Styles];

    #selectRef = createRef<HTMLSelectElement>();

    //#region Listeners

    /**
     * An event listener for when the user selects a different locale from the dropdown.
     *
     * Locale is fixed per page load: persist the choice and reload so the whole UI —
     * including server-rendered strings — comes back in the new locale.
     */
    protected localeChangeListener = (event: Event) => {
        const select = event.target as HTMLSelectElement;
        const nextActiveLanguageTag = select.value as TargetLanguageTag;

        this.blur();

        if (nextActiveLanguageTag === this.activeLanguageTag) return;

        applyLocaleChange(nextActiveLanguageTag);
    };

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

    //#region Render

    protected override render() {
        const activeLocaleTag = this.activeLanguageTag;
        const debug = this.can(CapabilitiesEnum.CanDebug);

        return guard([activeLocaleTag, debug], () => {
            const entries = formatLocaleDisplayNames(activeLocaleTag, {
                debug,
            });

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
                    @change=${this.localeChangeListener}
                    class="ak-m-capitalize"
                    name="locale"
                >
                    ${LocaleOptions({ entries, activeLocaleTag })}
                </select>`;
        });
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-locale-select": AKLocaleSelect;
    }
}
