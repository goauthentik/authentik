import "#elements/banner/Banner";

import { aki } from "#common/api/client";

import { AKElement } from "#elements/Base";

import { P4Disposition } from "#styles/patternfly/constants";

import { AdminApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

/**
 * Non-dismissible sticky admin banner shown when no base URL has been configured,
 * prompting an administrator to set it in the system settings
 */
@customElement("ak-base-url-banner")
export class BaseURLBanner extends AKElement {
    @state()
    protected configured: boolean | null = null;

    public refresh = () => {
        return aki(AdminApi)
            .adminSystemRetrieve()
            .then((info) => {
                this.configured = !!info.baseUrl;
            })
            .catch(() => {
                // Don't nag if we can't determine the state.
                this.configured = true;
            });
    };

    async firstUpdated(): Promise<void> {
        this.refresh();
    }

    render() {
        if (this.configured === null || this.configured) {
            return null;
        }

        return html`<ak-banner
            dismiss-key="base-url-banner"
            level=${P4Disposition.Warning}
            action-href="#/admin/settings"
            action-label=${msg("Configure it in the system settings", {
                id: "settings.base-url.banner.action",
            })}
        >
            ${msg("The base URL has not been configured.", {
                id: "settings.base-url.banner.label",
            })}
        </ak-banner>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-base-url-banner": BaseURLBanner;
    }
}
