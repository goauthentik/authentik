import {
    AdminStatus,
    AdminStatusCard,
} from "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { AdminApi, OutpostsApi, System } from "@goauthentik/api";

@customElement("ak-admin-status-system")
export class SystemStatusCard extends AdminStatusCard<System> {
    now?: Date;

    icon = "pf-icon pf-icon-server";

    @state()
    statusSummary?: string;

    async getPrimaryValue(): Promise<System> {
        this.now = new Date();
        let status = await new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
        if (status.embeddedOutpostHost === "" || !status.embeddedOutpostHost.includes("http")) {
            // First install, ensure the embedded outpost host is set
            // also run when outpost host does not contain http
            // (yes it's called host and requires a URL, i know)
            // TODO: Improve this in OOB flow
            await this.setOutpostHost();
            status = await new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
        }
        return status;
    }

    // Called on fresh installations and whenever the embedded outpost is deleted
    // automatically send the login URL when the user first visits the admin dashboard.
    async setOutpostHost(): Promise<void> {
        const outposts = await new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesList({
            managedIexact: "goauthentik.io/outposts/embedded",
        });
        if (outposts.results.length < 1) {
            return;
        }
        const outpost = outposts.results[0];
        outpost.config["authentik_host"] = window.location.origin;
        await new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesUpdate({
            uuid: outpost.pk,
            outpostRequest: outpost,
        });
    }

    getStatus(value: System): Promise<AdminStatus> {
        if (value.embeddedOutpostHost === "") {
            this.statusSummary = msg("Warning");
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg("Embedded outpost is not configured correctly.")}
                    <a href="#/outpost/outposts">${msg("Check outposts.")}</a>`,
            });
        }
        if (!value.httpIsSecure && document.location.protocol === "https:") {
            this.statusSummary = msg("Warning");
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg("HTTPS is not detected correctly")}`,
            });
        }
        const timeDiff = value.serverTime.getTime() - (this.now || new Date()).getTime();
        if (timeDiff > 5000 || timeDiff < -5000) {
            this.statusSummary = msg("Warning");
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: html`${msg("Server and client are further than 5 seconds apart.")}`,
            });
        }
        this.statusSummary = msg("OK");
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: html`${msg("Everything is ok.")}`,
        });
    }

    renderHeader(): TemplateResult {
        return html`${msg("System status")}`;
    }

    renderValue(): TemplateResult {
        return html`${this.statusSummary}`;
    }
}
