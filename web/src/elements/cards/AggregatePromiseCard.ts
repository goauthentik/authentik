import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";
import { until } from "lit/directives/until";

import "../Spinner";
import { PFSize } from "../Spinner";
import { AggregateCard } from "./AggregateCard";

@customElement("ak-aggregate-card-promise")
export class AggregatePromiseCard extends AggregateCard {
    @property({ attribute: false })
    promise?: Promise<Record<string, unknown>>;

    promiseProxy(): Promise<TemplateResult> {
        if (!this.promise) {
            return new Promise<TemplateResult>(() => html``);
        }
        return this.promise.then((s) => {
            return html`<i class="fa fa-check-circle"></i>&nbsp;${s.toString()}`;
        });
    }

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(this.promiseProxy(), html`<ak-spinner size="${PFSize.Large}"></ak-spinner>`)}
        </p>`;
    }
}
