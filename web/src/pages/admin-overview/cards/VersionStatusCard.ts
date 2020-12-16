import { gettext } from "django";
import { customElement } from "lit-element";
import { Version } from "../../../api/version";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-version")
export class VersionStatusCard extends AdminStatusCard<Version> {

    getPrimaryValue(): Promise<Version> {
        return Version.get();
    }

    getStatus(value: Version): Promise<AdminStatus> {
        if (value.outdated) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext(`${value.version_latest} is available!`),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle",
                message: gettext("Up-to-date!")
            });
        }
    }

}
