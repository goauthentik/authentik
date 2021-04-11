import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import { SourcesApi, Task, TaskStatusEnum } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/ConfirmationForm";

@customElement("ak-admin-status-card-ldap-sync")
export class LDAPSyncStatusCard extends AdminStatusCard<Task> {

    @property()
    slug!: string;

    getPrimaryValue(): Promise<Task> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesLdapSyncStatus({
            slug: this.slug
        }).then((value) => {
            return value;
        }).catch(() => {
            return { status: TaskStatusEnum.Error } as Task;
        });
    }

    renderValue(): TemplateResult {
        return html`${t`Last sync: ${this.value?.taskFinishTimestamp?.toLocaleTimeString() || "-"}`}`;
    }

    getStatus(value: Task): Promise<AdminStatus> {
        if (value.status !== TaskStatusEnum.Successful) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fas fa-times-circle pf-m-danger",
                message: t`Sync failed.`,
            });
        }
        const now = new Date().getTime();
        const maxDelta = 3600000; // 1 hour
        if (!value || (now - value.taskFinishTimestamp.getTime()) > maxDelta) {
            // No sync or last sync was over maxDelta ago
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: t`Not synced.`,
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
            });
        }
    }

    renderHeaderLink(): TemplateResult {
        return html`<a href="#/core/sources/${this.slug}">
                <i class="fa fa-external-link-alt"> </i>
            </a>`;
    }

}
