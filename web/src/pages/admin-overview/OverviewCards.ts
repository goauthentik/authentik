import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { until } from "lit-html/directives/until";
import { Flow } from "../../api/flow";
import { Policy } from "../../api/policy";
import { Provider } from "../../api/provider";
import { AggregateCard } from "../../elements/cards/AggregateCard";
import { SpinnerSize } from "../../elements/Spinner";

interface AdminStatus {
    icon: string;
    message?: string;
}

abstract class AdminStatusCard extends AggregateCard {

    abstract getPrimaryCounter(): Promise<number>;

    abstract getStatus(counter: number): Promise<AdminStatus>;

    @property({type: Number})
    counter = 0;

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(this.getPrimaryCounter().then((c) => {
                this.counter = c;
                return this.getStatus(c);
            }).then((status) => {
                return html`<p class="ak-aggregate-card">
                    <i class="${status.icon}"></i> ${this.counter}
                </p>
                ${status.message ? html`<p class="subtext">${status.message}</p>` : html``}`;
            }), html`<ak-spinner size="${SpinnerSize.Large}"></ak-spinner>`)}
        </p>`;
    }
}

@customElement("ak-admin-status-card-provider")
export class ProviderStatusCard extends AdminStatusCard {

    getPrimaryCounter(): Promise<number> {
        return Provider.list({
            "application__isnull": true
        }).then((response) => {
            return response.pagination.count;
        });
    }

    getStatus(counter: number): Promise<AdminStatus> {
        if (counter > 0) {
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

@customElement("ak-admin-status-card-policy-unbound")
export class PolicyUnboundStatusCard extends AdminStatusCard {

    getPrimaryCounter(): Promise<number> {
        return Policy.list({
            "bindings__isnull": true,
            "promptstage__isnull": true,
        }).then((response) => {
            return response.pagination.count;
        });
    }

    getStatus(counter: number): Promise<AdminStatus> {
        if (counter > 0) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("Policies without binding exist."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

}

@customElement("ak-admin-status-card-policy-cache")
export class PolicyCacheStatusCard extends AdminStatusCard {

    getPrimaryCounter(): Promise<number> {
        return Policy.cached();
    }

    getStatus(counter: number): Promise<AdminStatus> {
        if (counter < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("No policies cached. Users may experience slow response times."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

    renderHeaderLink(): TemplateResult {
        return html`<ak-modal-button href="/administration/overview/cache/policy/">
            <a slot="trigger">
                <i class="fa fa-trash"> </i>
            </a>
            <div slot="modal"></div>
        </ak-modal-button>`;
    }

}

@customElement("ak-admin-status-card-flow-cache")
export class FlowCacheStatusCard extends AdminStatusCard {

    getPrimaryCounter(): Promise<number> {
        return Flow.cached();
    }

    getStatus(counter: number): Promise<AdminStatus> {
        if (counter < 1) {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-exclamation-triangle",
                message: gettext("No flows cached."),
            });
        } else {
            return Promise.resolve<AdminStatus>({
                icon: "fa fa-check-circle"
            });
        }
    }

    renderHeaderLink(): TemplateResult {
        return html`<ak-modal-button href="/administration/overview/cache/flow/">
            <a slot="trigger">
                <i class="fa fa-trash"> </i>
            </a>
            <div slot="modal"></div>
        </ak-modal-button>`;
    }

}
