import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { PFSize } from "@goauthentik/common/enums.js";
import { AggregateCard } from "@goauthentik/elements/cards/AggregateCard";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { state } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import { ResponseError } from "@goauthentik/api";

export interface AdminStatus {
    icon: string;
    message?: TemplateResult;
}

export abstract class AdminStatusCard<T> extends AggregateCard {
    @state()
    private dataPromise?: Promise<T>;

    @state()
    protected value?: T;

    abstract getPrimaryValue(): Promise<T>;
    abstract getStatus(value: T): Promise<AdminStatus>;

    constructor() {
        super();
        this.addEventListener(EVENT_REFRESH, () => this.requestUpdate());
    }

    connectedCallback(): void {
        super.connectedCallback();
        this.dataPromise = this.getPrimaryValue().then((value) => {
            this.value = value;
            return value;
        });
    }

    renderValue(): TemplateResult {
        return html`${this.value}`;
    }

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(
                this.dataPromise
                    ? this.dataPromise
                          .then((value) =>
                              this.getStatus(value).then(
                                  (status) => html`
                                      <p>
                                          <i class="${status.icon}"></i>&nbsp;${this.renderValue()}
                                      </p>
                                      ${status.message
                                          ? html`<p class="subtext">${status.message}</p>`
                                          : nothing}
                                  `,
                              ),
                          )
                          .catch(
                              (exc: ResponseError) => html`
                                  <p><i class="fa fa-times"></i>&nbsp;${exc.response.statusText}</p>
                                  <p class="subtext">${msg("Failed to fetch")}</p>
                              `,
                          )
                    : html`<ak-spinner size="${PFSize.Large}"></ak-spinner>`,
                html`<ak-spinner size="${PFSize.Large}"></ak-spinner>`,
            )}
        </p>`;
    }
}
