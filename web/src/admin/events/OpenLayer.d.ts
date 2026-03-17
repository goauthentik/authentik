import { type OlLayerVector } from "@openlayers-elements/core/ol-layer-vector";
import { type OlLayerOpenstreetmap } from "@openlayers-elements/maps/ol-layer-openstreetmap";
import { type OlSelect } from "@openlayers-elements/maps/ol-select";

declare global {
    interface HTMLElementTagNameMap {
        "ol-layer-vector": OlLayerVector;
        "ol-layer-openstreetmap": OlLayerOpenstreetmap;
        "ol-select": OlSelect;
    }
}
