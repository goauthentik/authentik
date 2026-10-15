import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

import { AKElement } from "#elements/Base";
import { WithVersion } from "#elements/mixins/version";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-version-banner")
export class VersionBanner extends WithVersion(AKElement) {
    static styles = [PFBanner];
    static styles = [PFBanner, PFFlex];

    render() {
        if (!this.version?.versionCurrent) return nothing;

        if (this.version.versionCurrent === import.meta.env.AK_VERSION) return nothing;

        return html`
            <div class="pf-c-banner pf-m-sticky pf-m-gold">
                <div class="pf-l-flex pf-m-space-items-sm">
                    <div class="pf-l-flex__item">
                        <span class="pf-screen-reader">${msg("Warning banner:")}</span>
                        <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                    </div>
                    <div class="pf-l-flex__item">
                        ${msg(
                            str`A newer version (${this.version.versionCurrent}) of the UI is available.`,
                        )}
                    </div>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-version-banner": VersionBanner;
    }
}
