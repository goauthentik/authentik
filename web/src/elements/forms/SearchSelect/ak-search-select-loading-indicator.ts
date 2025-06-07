import { AKElement } from "@goauthentik/elements/Base.js";
import { randomId } from "@goauthentik/elements/utils/randomId.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * @class SearchSelectLoadingIndicator
 * @element ak-search-select-loading-indicator
 *
 * Just a loading indicator to fill in while we wait for the view to settle
 *
 * ## Available CSS `part::`
 *
 * - @part ak-search-select: The main Patternfly div
 * - @part ak-search-select-toggle: The Patternfly inner div
 * - @part ak-search-select-wrapper: Yet another Patternfly inner div
 * - @part ak-search-select-loading-indicator: The input object that hosts the "Loading..." message
 */

@customElement("ak-search-select-loading-indicator")
export class SearchSelectLoadingIndicator extends AKElement {
    static get styles() {
        return [PFBase, PFFormControl, PFSelect];
    }

    connectedCallback() {
        super.connectedCallback();
        this.setAttribute("data-ouia-component-type", "ak-search-select-loading-indicator");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());
        this.setAttribute("data-ouia-component-safe", "true");
    }

    render() {
        return html`
            <div class="pf-c-select" part="ak-search-select">
                <div class="pf-c-select__toggle pf-m-typeahead" part="ak-search-select-toggle">
                    <div class="pf-c-select__toggle-wrapper" part="ak-search-select-wrapper">
                        <input
                            class="pf-c-form-control pf-c-select__toggle-typeahead"
                            part="ak-search-select-loading-indicator"
                            type="text"
                            disabled
                            readonly
                            tabindex="-1"
                            value=${msg("Loading...")}
                        />
                    </div>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-loading-indicator": SearchSelectLoadingIndicator;
    }
}
