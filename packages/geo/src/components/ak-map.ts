import { buildHexworldStyle, wedgeColors } from "../hexworld/style.ts";
import {
    binAtLocation,
    buildEventFeatures,
    type EventFeatureCollection,
} from "../hexworld/wedges.ts";
import { type BasemapTheme, buildBasemapStyle, type FlavorName } from "../style.ts";
import Styles from "./ak-map.css";

import { EventActions } from "@goauthentik/api/src/models/EventActions.ts";

import { cellToLatLng } from "h3-js";
import maplibregl, { type LngLatBoundsLike, type Map as MapLibreMap } from "maplibre-gl";
import { Protocol } from "pmtiles";

import { LitElement, type PropertyValues, unsafeCSS } from "lit";
import { customElement, property } from "lit/decorators.js";

import MaplibreStyles from "maplibre-gl/dist/maplibre-gl.css";

export interface MapMarker {
    id: string;
    lon: number;
    lat: number;
    /** Event action coloring the column wedge. */
    action?: EventActions;
}

export interface BinSelectDetail {
    /** H3 cell id of the clicked column. */
    cell: string;
    /** Marker ids binned into the column at the current zoom band. */
    ids: string[];
}

const DEFAULT_FIT_PADDING = 64;
const MAX_FIT_ZOOM = 4.5;
// Initial view when no markers dictate one: central Europe, close enough that
// the globe fills the panel rather than floating in it.
const DEFAULT_CENTER: [number, number] = [-95.7129, 37.0902];
const DEFAULT_ZOOM = 2;
// Extruded event columns are invisible from straight overhead.
const DEFAULT_PITCH = 20;
const DEFAULT_MIN_ZOOM = 2;
// The bundled archive tops out at z7; allow a little overzoom (the simplified
// coast stays smooth) but cap it so labels/roads don't thin out into nothing.
const DEFAULT_MAX_ZOOM = 10;

// Register the pmtiles:// protocol once per document, lazily.
let pmtilesProtocolRegistered = false;

function ensurePMtilesProtocol(): void {
    if (pmtilesProtocolRegistered) return;

    maplibregl.addProtocol("pmtiles", new Protocol().tile);
    pmtilesProtocolRegistered = true;
}

@customElement("ak-map")
export class AKMap extends LitElement {
    public static readonly EVENTS_SOURCE = "events";
    public static readonly EVENTS_LAYER = "event-columns";
    public static styles = [
        // ---
        unsafeCSS(MaplibreStyles),
        unsafeCSS(Styles),
    ];

    /**
     * URL of a conventional PMTiles basemap archive (Protomaps schema).
     * Empty triggers hexworld mode with `hexworldURL` — the zero-config default.
     */
    @property({ type: String, attribute: "pmtiles-url" })
    public pmtilesURL: string | null = null;

    /**
     * URL of the bundled hexworld PMTiles archive (used when `pmtilesURL` is empty).
     */
    @property({ type: String, attribute: "hexworld-url" })
    public hexworldURL = "/static/dist/assets/maps/hexworld.pmtiles";

    @property({ type: String })
    public theme: BasemapTheme = "light";

    /**
     * Optional explicit flavor; overrides `theme` (light/dark/grayscale/black).
     */
    @property({ type: String })
    public flavor: FlavorName | null = null;

    @property({ type: String, attribute: "lang" })
    public lang = "en";

    @property({ type: Number, attribute: "max-zoom" })
    public maxZoom = DEFAULT_MAX_ZOOM;

    @property({ type: Number, attribute: "min-zoom" })
    public minZoom = DEFAULT_MIN_ZOOM;

    @property({ type: Number, attribute: "fit-padding" })
    public fitPadding = DEFAULT_FIT_PADDING;

    @property({ type: Number, attribute: "max-fit-zoom" })
    public maxFitZoom = MAX_FIT_ZOOM;

    @property({ attribute: false })
    public markers: MapMarker[] = [];

    /**
     * Formats an event action into its localized popup label.
     */
    @property({ attribute: false })
    public kindFormatter: (kind: string) => string | undefined = (kind) => kind;

    protected mapContainer: HTMLDivElement;

    protected map: MapLibreMap | null = null;

    #mapCreatedThisCycle = false;
    #mapReady = false;

    #columnSyncQueued = false;
    #columnSignature = "";
    #columnGrowthFrameID = 0;

    #popup: maplibregl.Popup | null = null;
    #hoverCell = "";

    get #hexworldMode(): boolean {
        return !this.pmtilesURL?.trim();
    }

    constructor() {
        super();

        this.mapContainer = this.ownerDocument.createElement("div");
        this.mapContainer.id = "map";
        this.mapContainer.part.add("map");
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.destroyMap();
    }

    protected override firstUpdated(): void {
        this.loadMap();
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
            this.applyStyle();
        }

        if (changed.has("maxZoom")) {
            this.map.setMaxZoom(this.maxZoom);
        }

        if (changed.has("minZoom")) {
            this.map.setMinZoom(this.minZoom);
        }

        if (changed.has("markers") && this.markersChanged()) {
            this.fitToMarkers();
            this.syncEventColumns();
        }
    }

    protected override render(): HTMLElement {
        return this.mapContainer;
    }

    protected loadMap() {
        if (this.map) return;

        ensurePMtilesProtocol();

        this.#mapCreatedThisCycle = true;

        this.map = new maplibregl.Map({
            container: this.mapContainer,
            style: this.createStyleSpec(),
            attributionControl: { compact: true },
            cooperativeGestures: false,
            center: DEFAULT_CENTER,
            zoom: DEFAULT_ZOOM,
            pitch: DEFAULT_PITCH,
            aroundCenter: true,
            minZoom: this.minZoom,
            maxZoom: this.maxZoom,
        });

        this.map.once("load", () => {
            this.#mapReady = true;
            this.mapContainer.classList.add("ready");
            this.markersChanged();
            this.fitToMarkers();
            this.syncEventColumns();
        });

        // Bins re-aggregate when the zoom band (H3 resolution) changes.
        this.map.on("zoomend", () => {
            this.hidePopup();
            this.syncEventColumns();
        });

        this.map.on("click", (event) => {
            const bin = this.binAt(event.point);

            if (!bin) return;

            this.dispatchEvent(
                new CustomEvent<BinSelectDetail>("bin-select", {
                    composed: true,
                    bubbles: true,
                    detail: bin,
                }),
            );
        });

        this.map.on("mousemove", (event) => {
            if (!this.map) return;

            const bin = this.binPointsAt(event.point);

            this.map.getCanvas().style.cursor = bin ? "pointer" : "";

            if (!bin) {
                this.hidePopup();
                return;
            }

            if (bin.cell !== this.#hoverCell) {
                this.showPopup(bin.cell, bin.points);
            }
        });

        this.map.on("mouseout", this.hidePopup);
    }

    protected showPopup(cell: string, points: MapMarker[]): void {
        if (!this.map) return;

        this.#hoverCell = cell;

        const [lat, lng] = cellToLatLng(cell);

        this.#popup ??= new maplibregl.Popup({
            closeButton: false,
            closeOnClick: false,
            anchor: "bottom",
            offset: 14,
        });

        this.#popup
            .setLngLat([lng, lat])
            .setDOMContent(this.createPopupContent(points))
            .addTo(this.map);
    }

    protected hidePopup = (): void => {
        this.#hoverCell = "";
        this.#popup?.remove();
    };

    protected createPopupContent(points: MapMarker[]): HTMLElement {
        const colors = wedgeColors(this.theme);
        const counts = new Map<EventActions, number>();

        for (const point of points) {
            const kind = point.action ?? EventActions.UnknownDefaultOpenApi;

            counts.set(kind, (counts.get(kind) ?? 0) + 1);
        }

        const root = this.ownerDocument.createElement("div");
        root.className = "ak-map-bin-popup";
        const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);

        for (const [kind, count] of sorted) {
            const row = this.ownerDocument.createElement("div");
            row.className = "kind";

            const dot = this.ownerDocument.createElement("span");

            dot.className = "dot";
            dot.style.background = colors[kind] || colors[EventActions.UnknownDefaultOpenApi] || "";

            const label = this.ownerDocument.createElement("span");

            label.textContent = `${count} × ${this.kindFormatter(kind)}`;

            row.append(dot, label);
            root.append(row);
        }

        return root;
    }

    /**
     * The event bin whose cell lies under a screen point, if it holds events.
     * Resolved via unproject + H3 math: fill-extrusion features are not
     * hit-testable under the globe projection (queryRenderedFeatures returns
     * nothing for them, observed on MapLibre 5.24), so the clickable area is
     * the column's ground footprint.
     */
    protected binPointsAt(point: maplibregl.Point): { cell: string; points: MapMarker[] } | null {
        if (!this.map || !this.map.getLayer(AKMap.EVENTS_LAYER)) {
            return null;
        }

        const { lat, lng } = this.map.unproject(point);
        const bin = binAtLocation(this.markers, this.map.getZoom(), lat, lng);

        if (!bin.points.length) return null;

        return bin;
    }

    protected binAt(point: maplibregl.Point): BinSelectDetail | null {
        const bin = this.binPointsAt(point);

        if (!bin) {
            return null;
        }

        return {
            cell: bin.cell,
            ids: bin.points.map((marker) => marker.id),
        };
    }

    protected destroyMap() {
        this.#markerSignature = "";
        this.#columnSignature = "";

        this.hidePopup();

        this.#popup = null;

        cancelAnimationFrame(this.#columnGrowthFrameID);

        this.map?.remove();
        this.map = null;
        this.#mapReady = false;
    }

    protected createStyleSpec() {
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

    protected eventColumnData(): EventFeatureCollection {
        return buildEventFeatures(this.markers, this.map?.getZoom() ?? 0);
    }

    protected ensureEventLayer(): void {
        if (!this.map || this.map.getSource(AKMap.EVENTS_SOURCE)) return;

        const colors = wedgeColors(this.theme);

        this.map.addSource(AKMap.EVENTS_SOURCE, {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
        });

        this.map.addLayer({
            id: AKMap.EVENTS_LAYER,
            type: "fill-extrusion",
            source: AKMap.EVENTS_SOURCE,
            paint: {
                "fill-extrusion-color": [
                    "match",
                    ["get", "action"],
                    EventActions.Login,
                    colors[EventActions.Login] || null,
                    EventActions.LoginFailed,
                    colors[EventActions.LoginFailed] || null,
                    EventActions.Logout,
                    colors[EventActions.Logout] || null,
                    EventActions.AuthorizeApplication,
                    colors[EventActions.AuthorizeApplication] || null,
                    colors[EventActions.UnknownDefaultOpenApi] || null,
                ],
                "fill-extrusion-height": ["get", "height"],
                "fill-extrusion-opacity": 0,
                "fill-extrusion-opacity-transition": { duration: 300 },
            },
        });

        // Kicks off the built-in paint transition from the initial 0.
        this.map.setPaintProperty(AKMap.EVENTS_LAYER, "fill-extrusion-opacity", 0.9);
        // Fresh (empty) source: unchanged data must still be re-applied.
        this.#columnSignature = "";
    }

    /**
     * Grow columns from the ground instead of popping in at full height.
     * `fill-extrusion-height` is data-driven, so MapLibre's paint transitions
     * cannot interpolate it; drive a scale factor through the expression by
     * hand instead.
     */
    protected animateColumns(from: number, to: number, duration: number, onDone?: () => void): void {
        cancelAnimationFrame(this.#columnGrowthFrameID);

        const start = performance.now();

        const step = (now: number) => {
            if (!this.map?.getLayer(AKMap.EVENTS_LAYER)) return;

            const t = Math.min(1, (now - start) / duration);
            const eased = 1 - Math.pow(1 - t, 3);
            const factor = from + (to - from) * eased;

            this.map.setPaintProperty(AKMap.EVENTS_LAYER, "fill-extrusion-height", [
                "*",
                ["get", "height"],
                factor,
            ]);

            if (t < 1) {
                this.#columnGrowthFrameID = requestAnimationFrame(step);
            } else {
                onDone?.();
            }
        };

        this.#columnGrowthFrameID = requestAnimationFrame(step);
    }

    protected growColumns(): void {
        this.animateColumns(0, 1, 450);
    }

    protected syncEventColumns(): void {
        if (!this.map || !this.#mapReady) return;

        // Never touch a style that is mid-swap: an exception escaping our
        // zoomend listener inside MapLibre's render frame wedges the render
        // task queue for good. A swap also wipes our source/layer, so re-sync
        // (and re-create them) once the new style settles.
        if (!this.map.isStyleLoaded()) {
            if (!this.#columnSyncQueued) {
                this.#columnSyncQueued = true;

                this.map.once("idle", () => {
                    this.#columnSyncQueued = false;
                    this.syncEventColumns();
                });
            }

            return;
        }

        this.ensureEventLayer();
        const data = this.eventColumnData();

        // zoomend fires on every zoom gesture, but bins only change when the
        // zoom band flips; only a real data change warrants a redraw + regrow.
        const signature = data.features
            .map(
                (feature) =>
                    `${feature.properties.cell}:${feature.properties.action}:${feature.properties.height.toFixed(0)}`,
            )
            .join("|");

        if (signature === this.#columnSignature) return;

        const hadColumns = this.#columnSignature !== "";
        this.#columnSignature = signature;

        const source = this.map.getSource(AKMap.EVENTS_SOURCE) as
            | maplibregl.GeoJSONSource
            | undefined;

        if (hadColumns) {
            // Band change (or new data over old): sink the standing columns
            // into the ground, swap the bins at the bottom, and grow the new
            // resolution back up — one continuous motion instead of a snap.
            this.animateColumns(1, 0, 180, () => {
                source?.setData(data);
                this.growColumns();
            });
            return;
        }

        source?.setData(data);
        this.growColumns();
    }

    protected styleSwapQueued = false;

    protected applyStyle(): void {
        if (!this.map) return;

        this.hidePopup();

        // setStyle() while the current style is still parsing wedges MapLibre
        // (5.24) into a permanently empty style — this bites both the initial
        // load (a theme context resolving right after construction) and rapid
        // theme flips. Defer until the style settles; #styleSpec() reads the
        // live properties, so the latest requested theme always wins.
        if (!this.map.isStyleLoaded()) {
            if (!this.styleSwapQueued) {
                this.styleSwapQueued = true;

                this.map.once("idle", () => {
                    this.styleSwapQueued = false;
                    this.applyStyle();
                });
            }

            return;
        }

        this.map.setStyle(this.createStyleSpec(), { diff: false });

        // The swap discarded the events source/layer; the sync's style-loaded
        // guard defers this to the new style's idle, re-creating them with the
        // current theme's wedge colors.
        this.syncEventColumns();
    }

    #markerSignature = "";

    /**
     * Consumers tend to rebuild the markers array on every render (e.g. a
     * table refresh), which would re-run the camera fit each time. Only a
     * semantic change to the set is worth acting on.
     */
    protected markersChanged(): boolean {
        const signature = this.markers
            .map((m) => `${m.id}:${m.lon}:${m.lat}:${m.action ?? ""}`)
            .join("|");
        if (signature === this.#markerSignature) return false;
        this.#markerSignature = signature;
        return true;
    }

    protected fitToMarkers(): void {
        if (!this.map || !this.markers.length) return;

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
        "ak-map": AKMap;
    }
    interface HTMLElementEventMap {
        "bin-select": CustomEvent<BinSelectDetail>;
    }
}
