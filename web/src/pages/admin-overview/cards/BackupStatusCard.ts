import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { AdminApi, CapabilitiesEnum, StatusEnum } from "@goauthentik/api";

import { DEFAULT_CONFIG, config } from "../../../api/Config";
import { convertToTitle } from "../../../utils";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";

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
            case StatusEnum.Successful:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-check-circle pf-m-success",
                });
            case StatusEnum.Error:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-times-circle pf-m-danger",
                    message: html`${t`Backup finished with errors.`}`,
                });
            default:
                return Promise.resolve<AdminStatus>({
                    icon: "fa fa-exclamation-triangle pf-m-warning",
                    message: html`${t`Backup finished with warnings/backup not supported.`}`,
                });
        }
    }
}
