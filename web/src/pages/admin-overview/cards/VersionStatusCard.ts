import { gettext } from "django";
import { customElement, html, TemplateResult } from "lit-element";
import { Version } from "../../../api/Versions";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {

    getPrimaryValue(): Promise<Version> {
        return Version.get();
    }

    getStatus(value: Version): Promise<AdminStatus> {
        if (value.outdated) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext(`${value.version_latest} is available!`),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success",
                message: gettext("Up-to-date!")
            });
        }
    }

    renderValue(): TemplateResult {
        return html`${this.value?.version_current}`;
    }

}
