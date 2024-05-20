import {
    AdminStatus,
    AdminStatusCard,
} from "@goauthentik/admin/admin-overview/cards/AdminStatusCard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { AdminApi } from "@goauthentik/api";

@customElement("ak-admin-status-card-workers")
export class WorkersStatusCard extends AdminStatusCard<number> {
    icon = "pf-icon pf-icon-server";

    getPrimaryValue(): Promise<number> {
        return new AdminApi(DEFAULT_CONFIG).adminWorkersRetrieve().then((workers) => {
            return workers.count;
        });
    }

    renderHeader(): TemplateResult {
        return html`${msg("Workers")}`;
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-times-circle pf-m-danger",
                message: html`${msg("No workers connected. Background tasks will not run.")}`,
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
            });
        }
    }
}
