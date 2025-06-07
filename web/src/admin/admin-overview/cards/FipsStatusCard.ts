import {
    AdminStatus,
    AdminStatusCard,
} from "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { AdminApi, SystemInfo } from "@goauthentik/api";

type StatusContent = { icon: string; message: TemplateResult };

@customElement("ak-admin-fips-status-system")
export class FipsStatusCard extends AdminStatusCard<SystemInfo> {
    icon = "pf-icon pf-icon-server";

    @state()
    statusSummary?: string;

    async getPrimaryValue(): Promise<SystemInfo> {
        return await new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
    }

    setStatus(summary: string, content: StatusContent): Promise<AdminStatus> {
        this.statusSummary = summary;
        return Promise.resolve<AdminStatus>(content);
    }

    getStatus(value: SystemInfo): Promise<AdminStatus> {
        return value.runtime.opensslFipsEnabled
            ? this.setStatus(msg("OK"), {
                  icon: "fa fa-check-circle pf-m-success",
                  message: html`${msg("FIPS compliance: passing")}`,
              })
            : this.setStatus(msg("Unverified"), {
                  icon: "fa fa-info-circle pf-m-warning",
                  message: html`${msg("FIPS compliance: unverified")}`,
              });
    }

    renderHeader(): TemplateResult {
        return html`${msg("FIPS Status")}`;
    }

    renderValue(): TemplateResult {
        return html`${this.statusSummary}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-fips-status-system": FipsStatusCard;
    }
}
