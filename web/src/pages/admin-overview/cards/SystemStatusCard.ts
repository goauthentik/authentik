import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { AdminApi, System } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";

@customElement("ak-admin-status-system")
export class SystemStatusCard extends AdminStatusCard<System> {
    now?: Date;

    header = "OK";

    getPrimaryValue(): Promise<System> {
        this.now = new Date();
        return new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
    }

    getStatus(value: System): Promise<AdminStatus> {
        if (value.embeddedOutpostHost === "") {
            this.header = t`Warning`;
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${t`Embedded outpost is not configured correctly.`}
                    <a href="#/outpost/outposts">${t`Check outposts.`}</a>`,
            });
        }
        if (!value.httpIsSecure && document.location.protocol === "https:") {
            this.header = t`Warning`;
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${t`HTTPS is not detected correctly`}`,
            });
        }
        const timeDiff = value.serverTime.getTime() - (this.now || new Date()).getTime();
        if (timeDiff > 5000 || timeDiff < -5000) {
            this.header = t`Warning`;
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${t`Server and client are further than 5 seconds apart.`}`,
            });
        }
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: html`${t`Everything is ok.`}`,
        });
    }

    renderValue(): TemplateResult {
        return html`${this.header}`;
    }
}
