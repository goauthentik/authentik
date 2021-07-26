import { t } from "@lingui/macro";
import { customElement, html, TemplateResult } from "lit-element";
import { AdminApi, System } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-system")
export class SystemStatusCard extends AdminStatusCard<System> {

    now?: Date;

    header = "OK";

    getPrimaryValue(): Promise<System> {
        this.now = new Date();
        return new AdminApi(DEFAULT_CONFIG).adminSystemRetrieve();
    }

    getStatus(value: System): Promise<AdminStatus> {
        if (!value.httpIsSecure && document.location.protocol === "https:") {
            this.header = t`Warning`;
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: t`HTTPS is not detected correctly`,
            });
        }
        const timeDiff = value.serverTime.getTime() - (this.now || new Date()).getTime();
        console.log(`authentik/: timediff ${timeDiff}`);
        if (timeDiff > 5000 || timeDiff < -5000) {
            this.header = t`Warning`;
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: t`Server and client are further than 5 seconds apart.`,
            });
        }
        return Promise.resolve<AdminStatus>({
            icon: "fa fa-check-circle pf-m-success",
            message: t`Everything is ok.`
        });
    }

    renderValue(): TemplateResult {
        return html`${this.header}`;
    }

}
