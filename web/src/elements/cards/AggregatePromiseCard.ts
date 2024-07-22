import { PFSize } from "@goauthentik/common/enums.js";
import "@goauthentik/elements/Spinner";
import { AggregateCard, type IAggregateCard } from "@goauthentik/elements/cards/AggregateCard";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

export interface IAggregatePromiseCard extends IAggregateCard {
    promise?: Promise<Record<string, unknown>>;
    failureMessage?: string;
}

/**
 * class AggregatePromiseCard
 * element ak-aggregate-card-promise
 *
 * Card component with a specific layout for quick informational blurbs, fills in its main content
 * with the results of a promise; shows a spinner when the promise has not yet resolved. Inherits
 * from [AggregateCard](./AggregateCard.ts).
 */

@customElement("ak-aggregate-card-promise")
export class AggregatePromiseCard extends AggregateCard implements IAggregatePromiseCard {
    /**
     * If this contains an `fa-` style string, the FontAwesome icon specified will be shown next to
     * the header.
     *
     * @attr
     */
    @property({ attribute: false })
    promise?: Promise<Record<string, unknown>>;

    /**
     * The error message if the promise is rejected or throws an exception.
     *
     * @attr
     */
    @property()
    failureMessage = msg("Operation failed to complete");

    async promiseProxy(): Promise<TemplateResult | typeof nothing> {
        if (!this.promise) {
            return nothing;
        }
        try {
            const value = await this.promise;
            return html`<i class="fa fa-check-circle"></i>&nbsp;${value.toString()}`;
        } catch (error: unknown) {
            console.warn(error);
            return html`<i class="fa fa-exclamation-circle"></i>&nbsp;${this.failureMessage}`;
        }
    }

    renderInner(): TemplateResult {
        return html`<p class="center-value">
            ${until(this.promiseProxy(), html`<ak-spinner size="${PFSize.Large}"></ak-spinner>`)}
        </p>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-aggregate-card-promise": AggregatePromiseCard;
    }
}
