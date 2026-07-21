import "@goauthentik/geo/components/ak-map";

import { formatEventAction } from "#admin/events/labels";

import { EventWithContext } from "#common/events";

import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { PaginatedResponse } from "#elements/table/Table";

import { Event } from "@goauthentik/api";
import type { BinSelectDetail, MapMarker } from "@goauthentik/geo";

import { css, CSSResult, html, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

/**
 *
 * @event {select-events} - Fired when an event column is selected on the map. The ids of the
 *      column's events are contained in the `detail.eventIds` field.
 *
 */
@customElement("ak-events-map")
export class EventMap extends WithBrandConfig(AKElement) {
    public static styles: CSSResult[] = [
        PFCard,
        css`
            .pf-c-card,
            ak-map {
                display: block;
                height: 24rem;
            }
        `,
    ];

    @property({ attribute: false })
    public events?: PaginatedResponse<Event>;

    @property({ type: Number })
    public zoomPaddingPx = 100;

    private get markers(): MapMarker[] {
        const results = this.events?.results ?? [];

        return results
            .filter((event): event is EventWithContext => {
                const geo = (event as EventWithContext).context?.geo;
                return Boolean(geo && typeof geo.lat === "number" && typeof geo.long === "number");
            })
            .map((event) => {
                const geo = event.context.geo!;
                return {
                    id: String(event.pk),
                    lon: geo.long!,
                    lat: geo.lat!,
                    action: event.action,
                };
            });
    }

    #onBinSelect = (event: CustomEvent<BinSelectDetail>) => {
        this.dispatchEvent(
            new CustomEvent("select-events", {
                composed: true,
                bubbles: true,
                detail: { eventIds: event.detail.ids },
            }),
        );
    };

    render(): TemplateResult {
        const theme = this.activeTheme === "dark" ? "dark" : "light";
        // Empty brandingMapTiles flips ak-map into hexworld mode (the bundled
        // default); a non-empty value routes to the conventional basemap path.
        return html`<div class="pf-c-card">
            <ak-map
                pmtiles-url=${this.brandingMapTiles}
                theme=${theme}
                .markers=${this.markers}
                .kindFormatter=${formatEventAction}
                fit-padding=${this.zoomPaddingPx}
                @bin-select=${this.#onBinSelect}
            ></ak-map>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-map": EventMap;
    }
}
