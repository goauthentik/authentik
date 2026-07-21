import { cellCounts } from "../hexworld/events.js";
import { buildHexworldStyle } from "../hexworld/style.js";
import { type BasemapTheme, buildBasemapStyle, type FlavorName } from "../style.js";

import maplibregl, { type LngLatBoundsLike, type Map as MapLibreMap } from "maplibre-gl";
import { Protocol } from "pmtiles";

import { css, html, LitElement, type PropertyValues, unsafeCSS } from "lit";
import { customElement, property, query } from "lit/decorators.js";

import MaplibreStyles from "maplibre-gl/dist/maplibre-gl.css";

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
// Initial view when no markers dictate one: central Europe, close enough that
// the globe fills the panel rather than floating in it.
const DEFAULT_CENTER: [number, number] = [12, 50];
const DEFAULT_ZOOM = 2;
// The bundled archive tops out at z7; allow a little overzoom (the simplified
// coast stays smooth) but cap it so labels/roads don't thin out into nothing.
const DEFAULT_MAX_ZOOM = 10;

// Register the pmtiles:// protocol once per document, lazily.
let pmtilesProtocolRegistered = false;
function ensurePmtilesProtocol(): void {
    if (pmtilesProtocolRegistered) return;
    maplibregl.addProtocol("pmtiles", new Protocol().tile);
    pmtilesProtocolRegistered = true;
}

@customElement("ak-map")
export class AkMap extends LitElement {
    /**
     * URL of a conventional PMTiles basemap archive (Protomaps schema).
     * Empty triggers hexworld mode with `hexworldURL` — the zero-config default.
     */
    @property({ type: String, attribute: "pmtiles-url" })
    public pmtilesURL = "";

    /**
     * URL of the bundled hexworld PMTiles archive (used when `pmtilesURL` is empty).
     */
    @property({ type: String, attribute: "hexworld-url" })
    public hexworldURL = "/static/dist/assets/maps/hexworld.pmtiles";

    @property({ type: String })
    public theme: BasemapTheme = "light";

    /** Optional explicit flavor; overrides `theme` (light/dark/grayscale/black). */
    @property({ type: String })
    public flavor: FlavorName | null = null;

    @property({ type: String, attribute: "lang" })
    public lang = "en";

    @property({ type: Number, attribute: "max-zoom" })
    public maxZoom = DEFAULT_MAX_ZOOM;

    @property({ type: Number, attribute: "fit-padding" })
    public fitPadding = DEFAULT_FIT_PADDING;

    @property({ type: Number, attribute: "max-fit-zoom" })
    public maxFitZoom = MAX_FIT_ZOOM;

    @property({ attribute: false })
    public markers: MapMarker[] = [];

    @query("#map")
    private mapContainer?: HTMLDivElement;

    protected map?: MapLibreMap;

    #mapCreatedThisCycle = false;
    #mapReady = false;
    #markerInstances = new Map<string, maplibregl.Marker>();
    #litCells = new Set<string>();

    get #hexworldMode(): boolean {
        return !this.pmtilesURL.trim();
    }

    static styles = [
        unsafeCSS(MaplibreStyles),
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

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#destroyMap();
    }

    protected override firstUpdated(): void {
        this.#initialiseMap();
    }

    protected override updated(changed: PropertyValues<this>): void {
        if (!this.map) return;
        // The first updated() call after firstUpdated() reports every
        // initially-set property as changed, but the map was just constructed
        // from those exact values. Re-applying the style here means calling
        // setStyle() while the constructor's style is still parsing, which
        // MapLibre (observed on 5.24) answers with a permanently empty style.
        if (this.#mapCreatedThisCycle) {
            this.#mapCreatedThisCycle = false;
            return;
        }
        if (
            changed.has("pmtilesURL") ||
            changed.has("hexworldURL") ||
            changed.has("theme") ||
            changed.has("flavor") ||
            changed.has("lang")
        ) {
            this.#applyStyle();
        }
        if (changed.has("maxZoom")) {
            this.map.setMaxZoom(this.maxZoom);
        }
        if (changed.has("markers")) {
            this.#syncMarkers();
            this.#syncHexStates();
        }
    }

    render() {
        return html`<div id="map" part="map"></div>`;
    }

    #initialiseMap() {
        if (!this.mapContainer || this.map) return;
        ensurePmtilesProtocol();
        this.#mapCreatedThisCycle = true;
        this.map = new maplibregl.Map({
            container: this.mapContainer,
            style: this.#styleSpec(),
            attributionControl: { compact: true },
            cooperativeGestures: false,
            center: DEFAULT_CENTER,
            zoom: DEFAULT_ZOOM,
            maxZoom: this.maxZoom,
        });
        this.map.once("load", () => {
            this.#mapReady = true;
            this.#syncMarkers();
            this.#syncHexStates();
        });
        this.map.on("zoomend", () => this.#syncHexStates());
    }

    #destroyMap() {
        for (const marker of this.#markerInstances.values()) {
            marker.remove();
        }
        this.#markerInstances.clear();
        this.#litCells.clear();
        this.map?.remove();
        this.map = undefined;
        this.#mapReady = false;
    }

    #styleSpec() {
        if (this.#hexworldMode) {
            return buildHexworldStyle({ archiveURL: this.hexworldURL, theme: this.theme });
        }
        return buildBasemapStyle({
            pmtilesURL: this.pmtilesURL,
            theme: this.theme,
            flavor: this.flavor,
            lang: this.lang,
        });
    }

    #syncHexStates() {
        if (!this.map || !this.#mapReady || !this.#hexworldMode) return;
        const target = { source: "hexworld", sourceLayer: "hex" } as const;
        for (const cell of this.#litCells) {
            this.map.removeFeatureState({ ...target, id: cell });
        }
        this.#litCells.clear();
        const counts = cellCounts(this.markers, this.map.getZoom());
        for (const [cell, events] of counts) {
            this.map.setFeatureState({ ...target, id: cell }, { events });
            this.#litCells.add(cell);
        }
    }

    #applyStyle() {
        this.map?.setStyle(this.#styleSpec(), { diff: false });
    }

    #syncMarkers() {
        if (!this.map || !this.#mapReady) return;

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
            instance.addTo(this.map);
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
        if (!this.map || this.markers.length === 0) return;
        const lons = this.markers.map((m) => m.lon);
        const lats = this.markers.map((m) => m.lat);
        const bounds: LngLatBoundsLike = [
            [Math.min(...lons), Math.min(...lats)],
            [Math.max(...lons), Math.max(...lats)],
        ];
        this.map.fitBounds(bounds, {
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
