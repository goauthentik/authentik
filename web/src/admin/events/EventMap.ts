import { EventGeo } from "@goauthentik/admin/events/utils";
import { AKElement } from "@goauthentik/elements/Base";
import "@openlayers-elements/core/ol-layer-vector";
import "@openlayers-elements/core/ol-map";
import "@openlayers-elements/maps/ol-control";
import "@openlayers-elements/maps/ol-layer-openstreetmap";
import "@openlayers-elements/maps/ol-marker-icon";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PaginatedEventList } from "@goauthentik/api";

@customElement("ak-events-map")
export class EventMap extends AKElement {
    @property({ attribute: false })
    events?: PaginatedEventList;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFCard,
            css`
                ol-map {
                    height: 25em;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
                <ol-map>
                    <ol-layer-openstreetmap></ol-layer-openstreetmap>
                    <ol-layer-vector>
                        ${this.events
                            ? html`
                                  ${this.events.results
                                      .filter((event) => {
                                          return Object.hasOwn(event.context, "geo");
                                      })
                                      .map((event) => {
                                          const geo = event.context.geo as unknown as EventGeo;
                                          return html`<ol-marker-icon
                                              src="https://openlayers-elements.netlify.app/assets/icon.png"
                                              lon=${geo.long}
                                              lat=${geo.lat}
                                          ></ol-marker-icon>`;
                                      })}
                              `
                            : nothing}
                    </ol-layer-vector>
                </ol-map>
        </div>`;
    }
}
