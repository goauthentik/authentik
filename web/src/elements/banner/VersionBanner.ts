import { WithVersion } from "#elements/mixins/version";
import { AKElement } from "@goauthentik/elements/Base";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-version-banner")
export class VersionBanner extends WithVersion(AKElement) {
    static styles = [PFBanner];

    render() {
        if (!this.version?.versionCurrent) return nothing;
        if (this.version.versionCurrent === import.meta.env.AK_VERSION) return nothing;

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
