import { gettext } from "django";
import { customElement } from "lit-element";
import { AdminApi } from "../../../api";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { AdminStatus, AdminStatusCard } from "./AdminStatusCard";

@customElement("ak-admin-status-card-workers")
export class WorkersStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return new AdminApi(DEFAULT_CONFIG).adminWorkersList({}).then((workers) => {
            return workers.pagination.count;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle pf-m-warning",
                message: gettext("No workers connected. Background tasks will not run."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle pf-m-success"
            });
        }
    }

}
