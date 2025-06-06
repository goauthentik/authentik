import { EventWithContext } from "#common/events";
import { globalAK } from "#common/global";
import { AKElement } from "@goauthentik/elements/Base";
import "@openlayers-elements/core/ol-layer-vector";
import LayerVector from "ol/layer/Vector";
import "@openlayers-elements/core/ol-map";
import type OlMap from "@openlayers-elements/core/ol-map";
import "@openlayers-elements/maps/ol-control";
import "@openlayers-elements/maps/ol-layer-openstreetmap";
import "@openlayers-elements/maps/ol-marker-icon";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, query } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PaginatedEventList } from "@goauthentik/api";

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

    registered = false

    updated() {
        if (this.registered) {return}
        if (!this.map?.map) {return}
        this.map.map.on("click", (ev) => {
            this.map?.map.forEachFeatureAtPixel(
                ev.pixel,
                (feature) => {
                    console.log(feature);
                    return;
                },
                {
                    layerFilter: (layer) => {
                        return layer instanceof LayerVector;
                    },
                },
            );
        });
        this.registered = true;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <ol-map>
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
                                  return html`<ol-marker-icon
                                      src="${globalAK().api
                                          .base}static/dist/assets/images/map_pin.svg"
                                      lon=${geo.long!}
                                      lat=${geo.lat!}
                                      anchor-y=${1}
                                  ></ol-marker-icon>`;
                              })
                        : nothing}
                </ol-layer-vector>
            </ol-map>
        </div>`;
    }
}
