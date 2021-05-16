import { t } from "@lingui/macro";
import { customElement, html, TemplateResult } from "lit-element";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import { AdminApi, StatusEnum } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { convertToTitle } from "../../../utils";

@customElement("ak-admin-status-card-backup")
export class BackupStatusCard extends AdminStatusCard<StatusEnum> {

    getPrimaryValue(): Promise<StatusEnum> {
        return new AdminApi(DEFAULT_CONFIG).adminSystemTasksRetrieve({
            id: "backup_database"
        }).then((value) => {
            return value.status;
        }).catch(() => {
            return StatusEnum.Error;
        });
    }

    renderValue(): TemplateResult {
        return html`${convertToTitle(this.value?.toString() || "")}`;
    }

    getStatus(value: StatusEnum): Promise<AdminStatus> {
        switch (value) {
            case StatusEnum.Warning:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-exclamation-triangle pf-m-warning",
                    message: t`Backup finished with warnings.`,
                });
            case StatusEnum.Error:
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
