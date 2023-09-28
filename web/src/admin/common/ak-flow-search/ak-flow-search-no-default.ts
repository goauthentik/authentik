import "@goauthentik/elements/forms/SearchSelect";

import { html } from "lit";
import { customElement } from "lit/decorators.js";

import type { Flow } from "@goauthentik/api";

import { FlowSearch, getFlowValue, renderDescription, renderElement } from "./FlowSearch";

/**
 * @element ak-flow-search-no-default
 *
 * A variant of the Flow Search that doesn't look for a current flow-of-flowtype according to the
 * user's settings because there shouldn't be one. Currently only used for uploading providers via
 * metadata, as that scenario can only happen when no current instance is available.
 */

@customElement("ak-flow-search-no-default")
export class AkFlowSearchNoDefault<T extends Flow> extends FlowSearch<T> {
    render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .renderElement=${renderElement}
                .renderDescription=${renderDescription}
                .value=${getFlowValue}
                ?blankable=${!this.required}
            >
            </ak-search-select>
        `;
    }
}

export default AkFlowSearchNoDefault;
