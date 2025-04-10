import { VERSION } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { WithVersion } from "@goauthentik/elements/mixins/version";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-version-banner")
export class VersionBanner extends WithVersion(AKElement) {
    static get styles() {
        return [PFBanner];
    }

    render() {
        if (!this.version || this.version.versionCurrent === VERSION) {
            return nothing;
        }
        return html`
            <div class="pf-c-banner pf-m-sticky pf-m-gold">
                ${msg(
                    str`A newer version (${this.version.versionCurrent}) of the UI is available.`,
                )}
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-version-banner": VersionBanner;
    }
}
