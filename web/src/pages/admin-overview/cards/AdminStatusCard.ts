import { html, TemplateResult } from "lit-html";
import { until } from "lit-html/directives/until";
import { AggregateCard } from "../../../elements/cards/AggregateCard";
import { SpinnerSize } from "../../../elements/Spinner";

export interface AdminStatus {
    icon: string;
    message?: string;
}

export abstract class AdminStatusCard<T> extends AggregateCard {

    abstract getPrimaryValue(): Promise<T>;

    abstract getStatus(value: T): Promise<AdminStatus>;

    value?: T;

    constructor() {
        super();
        this.addEventListener("ak-refresh", () => {
            this.requestUpdate();
        });
    }

    renderValue(): TemplateResult {
        return html`${this.value}`;
    }

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(this.getPrimaryValue().then((v) => {
                this.value = v;
                return this.getStatus(v);
            }).then((status) => {
                return html`<p class="ak-aggregate-card">
                        <i class="${status.icon}"></i> ${this.renderValue()}
                    </p>
                    ${status.message ? html`<p class="subtext">${status.message}</p>` : html``}`;
            }), html`<ak-spinner size="${SpinnerSize.Large}"></ak-spinner>`)}
        </p>`;
    }
}

