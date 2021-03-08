import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { AdminApi, Version } from "../../../api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {

    getPrimaryValue(): Promise<Version> {
        return new AdminApi(DEFAULT_CONFIG).adminVersionList({});
    }

    getStatus(value: Version): Promise<AdminStatus> {
        if (value.outdated) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext(`${value.versionLatest} is available!`),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
                message: gettext("Up-to-date!")
            });
        }
    }

    renderValue(): TemplateResult {
        return html`${this.value?.versionCurrent}`;
    }

}
