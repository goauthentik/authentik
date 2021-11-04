import { TemplateResult, html } from "lit";
import { until } from "lit/directives/until.js";

import { EVENT_REFRESH } from "../../../constants";
import { PFSize } from "../../../elements/Spinner";
import { AggregateCard } from "../../../elements/cards/AggregateCard";

export interface AdminStatus {
    icon: string;
    message?: TemplateResult;
}

export abstract class AdminStatusCard<T> extends AggregateCard {
    abstract getPrimaryValue(): Promise<T>;

    abstract getStatus(value: T): Promise<AdminStatus>;

    value?: T;

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => {
            this.requestUpdate();
        });
    }

    renderValue(): TemplateResult {
        return html`${this.value}`;
    }

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(
                this.getPrimaryValue()
                    .then((v) => {
                        this.value = v;
                        return this.getStatus(v);
                    })
                    .then((status) => {
                        return html`<p><i class="${status.icon}"></i>&nbsp;${this.renderValue()}</p>
                            ${status.message
                                ? html`<p class="subtext">${status.message}</p>`
                                : html``}`;
                    }),
                html`<ak-spinner size="${PFSize.Large}"></ak-spinner>`,
            )}
        </p>`;
    }
}
