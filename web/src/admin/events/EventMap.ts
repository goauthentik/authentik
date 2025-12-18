import "@openlayers-elements/core/ol-layer-vector";
import "@openlayers-elements/maps/ol-layer-openstreetmap";
import "@openlayers-elements/maps/ol-select";

import { EventWithContext } from "#common/events";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { PaginatedResponse } from "#elements/table/Table";

import { Event } from "@goauthentik/api";

import type OlLayerVector from "@openlayers-elements/core/ol-layer-vector.js";
import OlMap from "@openlayers-elements/core/ol-map.js";
import { isEmpty } from "ol/extent.js";
import Feature from "ol/Feature.js";
import { Point } from "ol/geom.js";
import { fromLonLat } from "ol/proj.js";
import Icon from "ol/style/Icon.js";
import Style from "ol/style/Style.js";

import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property, query } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import OL from "ol/ol.css";

@customElement("ak-map")
export class Map extends OlMap {
    public render() {
        return html`
            <style>
                ${OL}
            </style>
            <style>
                :host {
                    display: block;
                }

                #map {
                    height: 100%;
                }
            </style>
            <div id="map"></div>
            <slot></slot>
        `;
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
    events?: PaginatedResponse<Event>;

    @query("ol-layer-vector")
    vectorLayer?: OlLayerVector;

    @query("ak-map")
    map?: Map;

    @property({ type: Number })
    zoomPaddingPx = 100;

    static styles: CSSResult[] = [
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

    updated(_changedProperties: PropertyValues<this>): void {
        if (!_changedProperties.has("events")) {
            return;
        }
        if (!this.vectorLayer?.source || !this.map?.map) {
            return;
        }
        // Remove all existing points
        this.vectorLayer.source.clear();
        // Re-add them
        this.events?.results
            .filter((event) => {
                if (!Object.hasOwn(event.context || {}, "geo")) {
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
        // Zoom to show points better
        if (isEmpty(this.vectorLayer.source.getExtent())) {
            return;
        }
        this.map.map.getView().fit(this.vectorLayer.source.getExtent(), {
            padding: [
                this.zoomPaddingPx,
                this.zoomPaddingPx,
                this.zoomPaddingPx,
                this.zoomPaddingPx,
            ],
            duration: 500,
            maxZoom: 4.5,
        });
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <ak-map>
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
            </ak-map>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-map": Map;
        "ak-events-map": EventMap;
    }
}
