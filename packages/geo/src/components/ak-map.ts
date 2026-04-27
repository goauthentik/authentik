import { LitElement, type PropertyValues, css, html, unsafeCSS } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import maplibregl, { type LngLatBoundsLike, type Map as MapLibreMap } from "maplibre-gl";
import maplibreCss from "maplibre-gl/dist/maplibre-gl.css";

import { type BasemapTheme, buildBasemapStyle } from "../style.js";

export interface MapMarker {
    id: string;
    lon: number;
    lat: number;
    icon?: string;
}

export interface MarkerSelectDetail {
    id: string;
}

const DEFAULT_FIT_PADDING = 64;
const MAX_FIT_ZOOM = 4.5;

@customElement("ak-map")
export class AkMap extends LitElement {
    @property({ type: String, attribute: "tile-url" })
    tileUrl = "/tiles/{z}/{x}/{y}.mvt";

    @property({ type: String })
    theme: BasemapTheme = "light";

    @property({ type: String, attribute: "lang" })
    lang = "en";

    @property({ type: Number, attribute: "fit-padding" })
    fitPadding = DEFAULT_FIT_PADDING;

    @property({ type: Number, attribute: "max-fit-zoom" })
    maxFitZoom = MAX_FIT_ZOOM;

    @property({ attribute: false })
    markers: MapMarker[] = [];

    @query("#map")
    private mapContainer?: HTMLDivElement;

    #map?: MapLibreMap;
    #mapReady = false;
    #markerInstances = new Map<string, maplibregl.Marker>();

    static styles = [
        unsafeCSS(maplibreCss),
        css`
            :host {
                display: block;
                height: 100%;
                width: 100%;
            }

            #map {
                height: 100%;
                width: 100%;
            }

            #map :is(.maplibregl-canvas, canvas) {
                outline: none;
            }
        `,
    ];

    disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#destroyMap();
    }

    firstUpdated(): void {
        this.#initialiseMap();
    }

    updated(changed: PropertyValues<this>): void {
        if (!this.#map) return;
        if (changed.has("tileUrl") || changed.has("theme") || changed.has("lang")) {
            this.#applyStyle();
        }
        if (changed.has("markers")) {
            this.#syncMarkers();
        }
    }

    render() {
        return html`<div id="map" part="map"></div>`;
    }

    #initialiseMap() {
        if (!this.mapContainer || this.#map) return;
        this.#map = new maplibregl.Map({
            container: this.mapContainer,
            style: this.#styleSpec(),
            attributionControl: { compact: true },
            cooperativeGestures: false,
            center: [0, 20],
            zoom: 1,
        });
        this.#map.once("load", () => {
            this.#mapReady = true;
            this.#syncMarkers();
        });
    }

    #destroyMap() {
        for (const marker of this.#markerInstances.values()) {
            marker.remove();
        }
        this.#markerInstances.clear();
        this.#map?.remove();
        this.#map = undefined;
        this.#mapReady = false;
    }

    #styleSpec() {
        return buildBasemapStyle({
            tileUrl: this.tileUrl,
            theme: this.theme,
            lang: this.lang,
        });
    }

    #applyStyle() {
        this.#map?.setStyle(this.#styleSpec(), { diff: false });
    }

    #syncMarkers() {
        if (!this.#map || !this.#mapReady) return;

        const incoming = new Map(this.markers.map((m) => [m.id, m]));

        for (const [id, marker] of this.#markerInstances) {
            if (!incoming.has(id)) {
                marker.remove();
                this.#markerInstances.delete(id);
            }
        }

        for (const marker of this.markers) {
            const existing = this.#markerInstances.get(marker.id);
            if (existing) {
                existing.setLngLat([marker.lon, marker.lat]);
                continue;
            }
            const instance = this.#buildMarker(marker);
            instance.addTo(this.#map);
            this.#markerInstances.set(marker.id, instance);
        }

        this.#fitToMarkers();
    }

    #buildMarker(marker: MapMarker): maplibregl.Marker {
        let element: HTMLElement | undefined;
        if (marker.icon) {
            const img = document.createElement("img");
            img.src = marker.icon;
            img.alt = "";
            img.style.cursor = "pointer";
            img.style.width = "24px";
            img.style.height = "24px";
            img.style.transform = "translateY(-50%)";
            element = img;
        }
        const instance = new maplibregl.Marker({ element });
        instance.setLngLat([marker.lon, marker.lat]);
        const target = element ?? instance.getElement();
        target.addEventListener("click", (event) => {
            event.stopPropagation();
            this.dispatchEvent(
                new CustomEvent<MarkerSelectDetail>("marker-select", {
                    composed: true,
                    bubbles: true,
                    detail: { id: marker.id },
                }),
            );
        });
        return instance;
    }

    #fitToMarkers() {
        if (!this.#map || this.markers.length === 0) return;
        const lons = this.markers.map((m) => m.lon);
        const lats = this.markers.map((m) => m.lat);
        const bounds: LngLatBoundsLike = [
            [Math.min(...lons), Math.min(...lats)],
            [Math.max(...lons), Math.max(...lats)],
        ];
        this.#map.fitBounds(bounds, {
            padding: this.fitPadding,
            duration: 500,
            maxZoom: this.maxFitZoom,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-map": AkMap;
    }
    interface HTMLElementEventMap {
        "marker-select": CustomEvent<MarkerSelectDetail>;
    }
}
