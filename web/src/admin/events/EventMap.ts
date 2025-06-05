import { EventWithContext } from "#common/events";
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
                                      src="https://openlayers-elements.netlify.app/assets/icon.png"
                                      lon=${geo.long!}
                                      lat=${geo.lat!}
                                  ></ol-marker-icon>`;
                              })
                        : nothing}
                </ol-layer-vector>
            </ol-map>
        </div>`;
    }
}
