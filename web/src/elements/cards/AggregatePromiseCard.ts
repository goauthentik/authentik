import { customElement, html, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { AggregateCard } from "./AggregateCard";

@customElement("pb-aggregate-card-promise")
export class AggregatePromiseCard extends AggregateCard {
    @property()
    promise?: Promise<string>;

    promiseProxy(): Promise<TemplateResult> {
        if (!this.promise) {
            return new Promise<TemplateResult>(() => html``);
        }
        return this.promise.then(s => {
            return html`<i class="fa fa-check-circle"></i> ${s}`;
        });
    }

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(this.promiseProxy(), html`<pb-spinner size="large"></pb-spinner>`)}
        </p>`;
    }

}
