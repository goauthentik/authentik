import { t } from "@lingui/macro";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";
import { AdminApi, StatusEnum, CapabilitiesEnum } from "@goauthentik/api";
import { config, DEFAULT_CONFIG } from "../../../api/Config";
import { convertToTitle } from "../../../utils";

@customElement("ak-admin-status-card-backup")
export class BackupStatusCard extends AdminStatusCard<StatusEnum> {
    getPrimaryValue(): Promise<StatusEnum> {
        return new AdminApi(DEFAULT_CONFIG)
            .adminSystemTasksRetrieve({
                id: "backup_database",
            })
            .then((value) => {
                return value.status;
            })
            .catch(() => {
                // On error (probably 404), check the config and see if the server
                // can even backup
                return config().then((c) => {
                    if (c.capabilities.includes(CapabilitiesEnum.Backup)) {
                        return StatusEnum.Error;
                    }
                    return StatusEnum.Warning;
                });
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
                    message: html`${t`Backup finished with warnings/backup not supported.`}`,
                });
            case StatusEnum.Error:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-times-circle pf-m-danger",
                    message: html`${t`Backup finished with errors.`}`,
                });
            default:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-check-circle pf-m-success",
                });
        }
    }
}
