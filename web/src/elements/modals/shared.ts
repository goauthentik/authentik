import { SlottedTemplateResult } from "#elements/types";

/**
 * An element that is designed to included in a dialog or other container that supports transclusion.
 */
export interface TransclusionElement extends Element {
    /**
     * An optional method to render a header for the element, which can be used
     * when the element is transcluded into a dialog or other container that supports headers.
     *
     * @param force Whether to force the contents to render.
     */
    renderHeader?(force?: boolean): SlottedTemplateResult;

    /**
     * An optional method to render action buttons for the element, which can be used
     * when the element is transcluded into a dialog or other container that supports action buttons.
     *
     * @param force Whether to force the contents to render.
     */
    renderActions?(force?: boolean): SlottedTemplateResult;

    /**
     * Whether the element should perform a viewport check before rendering.
     *
     * @deprecated Remove this after all modals are migrated to use the new dialog system, which handles this automatically.
     */
    viewportCheck?: boolean;
}

/**
 * Type predicate to determine if an element is a {@linkcode TransclusionElement}.
 *
 * @param element The element to check.
 */
export function isTransclusionElement(element: Element): element is TransclusionElement {
    return "renderHeader" in element || "renderActions" in element;
}
