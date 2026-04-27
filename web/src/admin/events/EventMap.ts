import "@goauthentik/geo/components/ak-map";

import { EventWithContext } from "#common/events";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { PaginatedResponse } from "#elements/table/Table";

import type { MapMarker, MarkerSelectDetail } from "@goauthentik/geo";
import { Event } from "@goauthentik/api";

import { css, CSSResult, html, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

/**
 *
 * @event {select-event} - Fired when an event is selected on the map. ID of the event is contained
 *      in the `Event.detail` field.
 *
 */
@customElement("ak-events-map")
export class EventMap extends WithBrandConfig(AKElement) {
    @property({ attribute: false })
    events?: PaginatedResponse<Event>;

    @property({ type: Number })
    zoomPaddingPx = 100;

    static styles: CSSResult[] = [
        PFCard,
        css`
            .pf-c-card,
            ak-map {
                height: 24rem;
            }
            ak-map {
                display: block;
            }
        `,
    ];

    private get markers(): MapMarker[] {
        const pinIcon = `${globalAK().api.base}static/dist/assets/images/map_pin.svg`;
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
                    icon: pinIcon,
                };
            });
    }

    #onMarkerSelect = (event: CustomEvent<MarkerSelectDetail>) => {
        this.dispatchEvent(
            new CustomEvent("select-event", {
                composed: true,
                bubbles: true,
                detail: { eventId: event.detail.id },
            }),
        );
    };

    render(): TemplateResult {
        const theme = this.activeTheme === "dark" ? "dark" : "light";
        return html`<div class="pf-c-card">
            <ak-map
                tile-url=${this.brandingMapTiles}
                theme=${theme}
                .markers=${this.markers}
                fit-padding=${this.zoomPaddingPx}
                @marker-select=${this.#onMarkerSelect}
            ></ak-map>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-map": EventMap;
    }
}
