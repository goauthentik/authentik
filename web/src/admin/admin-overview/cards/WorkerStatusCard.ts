import { DEFAULT_CONFIG } from "#common/api/config";

import { AdminStatus, AdminStatusCard } from "#admin/admin-overview/cards/AdminStatusCard";

import { TasksApi, Worker } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-admin-status-card-workers")
export class WorkersStatusCard extends AdminStatusCard<Worker[]> {
    icon = "pf-icon pf-icon-server";

    getPrimaryValue(): Promise<Worker[]> {
        return new TasksApi(DEFAULT_CONFIG).tasksWorkersList();
    }

    renderHeader(): TemplateResult {
        return html`${msg("Workers")}`;
    }

    getStatus(value: Worker[]): Promise<AdminStatus> {
        if (value.length < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-times-circle pf-m-danger",
                message: html`${msg("No workers connected. Background tasks will not run.")}`,
            });
        } else if (value.filter((w) => !w.versionMatching).length > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-times-circle pf-m-danger",
                message: html`${msg("Worker with incorrect version connected.")}`,
            });
        }
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
        });
    }

    renderValue() {
        return html`${this.value?.length}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-card-workers": WorkersStatusCard;
    }
}
