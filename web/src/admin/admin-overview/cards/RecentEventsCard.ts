import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/timestamp/ak-timestamp";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import Styles from "#admin/admin-overview/cards/RecentEventsCard.css";
import { SimpleEventTable } from "#admin/events/SimpleEventTable";

import { EventsEventsListRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

@customElement("ak-recent-events")
export class RecentEventsCard extends SimpleEventTable {
    public override role = "region";
    public override ariaLabel = msg("Recent events");
    public override label = msg("Events");

    public override expandable = false;
    // Rough approximate based on admin overview card height
    public override pageSize = 6;

    @property()
    order = "-created";

    async apiParameters(): Promise<Partial<EventsEventsListRequest>> {
        return {};
    }

    static styles: CSSResult[] = [
        // ---
        ...super.styles,
        PFCard,
        Styles,
    ];

    renderToolbar(): TemplateResult {
        return html`<h1 class="pf-c-card__title">
            <i class="pf-icon pf-icon-catalog" aria-hidden="true"></i>
            ${msg("Recent events")}
        </h1>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-recent-events": RecentEventsCard;
    }
}
