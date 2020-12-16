import { gettext } from "django";
import { customElement } from "lit-element";
import { Provider } from "../../../api/Providers";
import { AdminStatusCard, AdminStatus } from "./AdminStatusCard";

@customElement("ak-admin-status-card-provider")
export class ProviderStatusCard extends AdminStatusCard<number> {

    getPrimaryValue(): Promise<number> {
        return Provider.list({
            "application__isnull": true
        }).then((response) => {
            return response.pagination.count;
        });
    }

    getStatus(value: number): Promise<AdminStatus> {
        if (value > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("Warning: At least one Provider has no application assigned."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

}
