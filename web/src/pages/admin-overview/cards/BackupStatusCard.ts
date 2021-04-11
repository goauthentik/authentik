import { t } from "@lingui/macro";
import { customElement, html, TemplateResult } from "lit-element";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import { AdminApi, TaskStatusEnum } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { convertToTitle } from "../../../utils";

@customElement("ak-admin-status-card-backup")
export class BackupStatusCard extends AdminStatusCard<TaskStatusEnum> {

    getPrimaryValue(): Promise<TaskStatusEnum> {
        return new AdminApi(DEFAULT_CONFIG).adminSystemTasksRead({
            id: "backup_database"
        }).then((value) => {
            return value.status;
        }).catch(() => {
            return TaskStatusEnum.Error;
        });
    }

    renderValue(): TemplateResult {
        return html`${convertToTitle(this.value?.toString() || "")}`;
    }

    getStatus(value: TaskStatusEnum): Promise<AdminStatus> {
        switch (value) {
            case TaskStatusEnum.Warning:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-exclamation-triangle pf-m-warning",
                    message: t`Backup finished with warnings.`,
                });
            case TaskStatusEnum.Error:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-times-circle pf-m-danger",
                    message: t`Backup finished with errors.`,
                });
            default:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-check-circle pf-m-success"
                });
        }
    }

}
