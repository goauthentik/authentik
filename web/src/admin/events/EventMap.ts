import { EventWithContext } from "#common/events";
import { globalAK } from "#common/global";
import { PaginatedResponse } from "#elements/table/Table";
import { AKElement } from "@goauthentik/elements/Base";
import "@openlayers-elements/core/ol-layer-vector";
import type OlLayerVector from "@openlayers-elements/core/ol-layer-vector";
import "@openlayers-elements/core/ol-map";
import "@openlayers-elements/maps/ol-layer-openstreetmap";
import "@openlayers-elements/maps/ol-select";
import Feature from "ol/Feature";
import { Point } from "ol/geom";
import { fromLonLat } from "ol/proj";
import Icon from "ol/style/Icon";
import Style from "ol/style/Style";

import { CSSResult, PropertyValues, TemplateResult, css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Event } from "@goauthentik/api";

/**
 *
 * @event {select-event} - Fired when an event is selected on the map. ID of the event is contained
 *      in the `Event.detail` field.
 *
 */
@customElement("ak-events-map")
export class EventMap extends AKElement {
    @property({ attribute: false })
    events?: PaginatedResponse<Event>;

    @query("ol-layer-vector")
    vectorLayer?: OlLayerVector;

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

    updated(_changedProperties: PropertyValues<this>): void {
        if (!_changedProperties.has("events")) {
            return;
        }
        this.vectorLayer?.source?.clear();
        this.events?.results
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
            .forEach((event) => {
                const geo = (event as EventWithContext).context.geo!;
                const point = new Point(fromLonLat([geo.long!, geo.lat!]));
                const feature = new Feature({
                    geometry: point,
                });
                feature.setStyle(
                    new Style({
                        image: new Icon({
                            anchor: [0.5, 1],
                            offset: [0, 0],
                            opacity: 1,
                            scale: 1,
                            rotateWithView: false,
                            rotation: 0,
                            src: `${globalAK().api.base}static/dist/assets/images/map_pin.svg`,
                        }),
                    }),
                );
                feature.setId(event.pk);
                this.vectorLayer?.source?.addFeature(feature);
            });
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
                <ol-layer-vector></ol-layer-vector>
            </ol-map>
        </div>`;
    }
}
