import { EventWithContext } from "#common/events";
import { globalAK } from "#common/global";
import { AKElement } from "@goauthentik/elements/Base";
import "@openlayers-elements/core/ol-layer-vector";
import "@openlayers-elements/core/ol-map";
import type OlMap from "@openlayers-elements/core/ol-map";
import "@openlayers-elements/maps/ol-control";
import "@openlayers-elements/maps/ol-layer-openstreetmap";
import OlMarkerIcon from "@openlayers-elements/maps/ol-marker-icon";
import "@openlayers-elements/maps/ol-select";
import type Feature from "ol/Feature";
import { Point } from "ol/geom";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, query } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PaginatedEventList } from "@goauthentik/api";

@customElement("ak-map-element")
export class OLMarker extends OlMarkerIcon {
    createFeature(map: OlMap | undefined): Feature<Point> {
        const feature = super.createFeature(map);
        feature.setId(this.id);
        return feature;
    }
}

/**
 *
 * @event {select-event} - Fired when an event is selected on the map. ID of the event is contained
 *      in the `Event.detail` field.
 *
 */
@customElement("ak-events-map")
export class EventMap extends AKElement {
    @property({ attribute: false })
    events?: PaginatedEventList;

    @query("ol-map")
    map?: OlMap;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFCard,
            css`
                .pf-c-card,
                ol-map {
                    height: 24rem;
                }
                :host([theme="dark"]) ol-map {
                    filter: invert(100%) hue-rotate(180deg);
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <ol-map>
                <ol-select
                    @feature-selected=${(ev: CustomEvent<{ feature: Feature }>) => {
                        const eventId = ev.detail.feature.getId();
                        this.dispatchEvent(
                            new CustomEvent("select-event", {
                                composed: true,
                                bubbles: true,
                                detail: {
                                    eventId: eventId,
                                },
                            }),
                        );
                    }}
                ></ol-select>
                <ol-layer-openstreetmap></ol-layer-openstreetmap>
                <ol-layer-vector>
                    ${this.events
                        ? this.events.results
                              .filter((event) => {
                                  if (!Object.hasOwn(event.context, "geo")) {
                                      return false;
                                  }
                                  const geo = (event as EventWithContext).context.geo;
                                  if (!geo?.lat || !geo.long) {
                                      return false;
                                  }
                                  return true;
                              })
                              .map((event) => {
                                  const geo = (event as EventWithContext).context.geo!;
                                  return html`<ak-map-element
                                      src="${globalAK().api
                                          .base}static/dist/assets/images/map_pin.svg"
                                      lon=${geo.long!}
                                      lat=${geo.lat!}
                                      anchor-y="1"
                                      id=${event.pk}
                                  ></ak-map-element>`;
                              })
                        : nothing}
                </ol-layer-vector>
            </ol-map>
        </div>`;
    }
}
