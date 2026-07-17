import "#elements/banner/Banner";

import { aki } from "#common/api/client";

import { BannerLevel } from "#elements/banner/Banner";
import { AKElement } from "#elements/Base";

import { AdminApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

/**
 * Non-dismissible sticky admin banner shown when no base URL has been configured,
 * prompting an administrator to set it in the system settings
 */
@customElement("ak-base-url-banner")
export class BaseURLBanner extends AKElement {
    @state()
    protected configured = true;

    async firstUpdated(): Promise<void> {
        try {
            const info = await aki(AdminApi).adminSystemRetrieve();
            this.configured = Boolean(info.baseUrl);
        } catch {
            // Don't nag if we can't determine the state.
            this.configured = true;
        }
    }

    render() {
        if (this.configured) return nothing;

        return html`
            <ak-banner
                level=${BannerLevel.Warning}
                action-href="#/admin/settings"
                action-label=${msg("Configure it in the system settings", {
                    id: "settings.base-url.banner.action",
                })}
            >
                ${msg("The base URL has not been configured.", {
                    id: "settings.base-url.banner.label",
                })}
            </ak-banner>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-base-url-banner": BaseURLBanner;
    }
}
