import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/cards/AggregateCard.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

import PFList from "@patternfly/patternfly/components/List/list.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export type QuickAction = [label: string, url: string, isExternal?: boolean];

export interface IQuickActionsCard {
    title?: string;
    actions: QuickAction[];
}

/**
 * class QuickActionsCard
 * element ak-quick-actions-card
 *
 * Specialized card for navigation.
 */
@customElement("ak-quick-actions-card")
export class QuickActionsCard extends AKElement implements IQuickActionsCard {
    static get styles() {
        return [PFBase, PFList];
    }

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
        const renderItem = ([label, url, external]: QuickAction) =>
            html` <li>
                <a class="pf-u-mb-xl" href=${url} ${external ? 'target="_blank"' : ""}>
                    ${external
                        ? html`${label}&nbsp;<i
                                  class="fas fa-external-link-alt ak-external-link"
                              ></i>`
                        : label}
                </a>
            </li>`;

        return html` <ak-aggregate-card icon="fa fa-share" header=${this.title} left-justified>
            <ul class="pf-c-list">
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
