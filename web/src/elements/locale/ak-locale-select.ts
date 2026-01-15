import { TargetLanguageTag } from "#common/ui/locale/definitions";
import { formatLocaleDisplayNames } from "#common/ui/locale/format";
import { setSessionLocale } from "#common/ui/locale/utils";

import { AKElement } from "#elements/Base";
import Styles from "#elements/locale/ak-locale-select.css";
import { LocaleOptions } from "#elements/locale/utils";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLocale } from "#elements/mixins/locale";

import { CapabilitiesEnum } from "@goauthentik/api";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail, msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { createRef, ref } from "lit/directives/ref.js";

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
        const locale = select.value as TargetLanguageTag;

        this.blur();

        requestAnimationFrame(() => {
            this.activeLanguageTag = locale;
            setSessionLocale(locale);
        });
    };

    #localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status !== "ready") {
            return;
        }

        if (!this.ready) {
            this.ready = true;
            window.clearTimeout(this.#readyTimeout);
        }
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

    //#region Lifecycle

    /**
     * Indicates whether the locale select is ready to be displayed.
     *
     * @remarks
     *
     * This avoids showing the select before the locale is initialized,
     * preventing a flash of unlocalized content and avoiding expensive localization
     * operations during initial render.
     */
    @state()
    protected ready = false;

    #readyTimeout = -1;
    #selectRef = createRef<HTMLSelectElement>();

    public override connectedCallback(): void {
        super.connectedCallback();

        this.addEventListener("click", this.show);

        window.addEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener, {
            once: true,
            passive: true,
        });
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        window.clearTimeout(this.#readyTimeout);
        window.removeEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);
    }

    public override firstUpdated(changed: PropertyValues<this>): void {
        super.firstUpdated(changed);

        // Fallback to ready if the network is taking too long.
        this.#readyTimeout = window.setTimeout(() => {
            this.ready = true;
            window.removeEventListener(LOCALE_STATUS_EVENT, this.#localeStatusListener);
        }, 250);
    }

    //#endregion

    //#region Render

    protected override render() {
        if (!this.ready) {
            return null;
        }

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
                    @change=${this.#localeChangeListener}
                    class="pf-c-form-control ak-m-capitalize"
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
