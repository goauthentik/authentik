import "#elements/cards/AggregateCard";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { map } from "lit/directives/map.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

export type QuickAction = [label: string, url: string, isExternal?: boolean];

export interface IQuickActionsCard {
    title?: string;
    actions: QuickAction[];
}

function renderItem([label, url, external]: QuickAction) {
    return html` <li>
        <a class="pf-u-mb-xl" href=${url} target=${ifDefined(external ? "_blank" : undefined)}
            >${label}${external
                ? html`&nbsp;<i
                          aria-hidden="true"
                          class="fas fa-external-link-alt ak-external-link"
                      ></i>`
                : nothing}
        </a>
    </li>`;
}

/**
 * class QuickActionsCard
 * element ak-quick-actions-card
 *
 * Specialized card for navigation.
 */
@customElement("ak-quick-actions-card")
export class QuickActionsCard extends AKElement implements IQuickActionsCard {
    static styles = [PFList];

    /**
     * Card title
     *
     * @attr
     */
    @property()
    title = msg("Quick actions");

    /**
     * Card contents. An array of [label, url, isExternal].  External links will
     * be rendered with an external link icon and will always open in a new tab.
     *
     * @attr
     */
    @property({ type: Array })
    actions: QuickAction[] = [];

    render() {
        return html` <ak-aggregate-card icon="fa fa-share" label=${this.title}>
            <ul aria-label="${msg("Quick actions")}" class="pf-c-list">
                ${map(this.actions, renderItem)}
            </ul>
        </ak-aggregate-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-quick-actions-card": QuickActionsCard;
    }
}
