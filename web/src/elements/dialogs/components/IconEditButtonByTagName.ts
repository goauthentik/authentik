import {
    defaultIconEditButtonProps,
    IconEditButton,
    type IconEditButtonProps,
} from "#elements/dialogs/components/IconEditButton";
import { lookupElementConstructor } from "#elements/dialogs/directives";
import type { SlottedTemplateResult } from "#elements/types";

/**
 * A helper function to render an edit button by looking up a custom element constructor based on a tag name.
 *
 * @param tagName The tag name of the custom element to look up and render in the modal.
 * @param instancePk The primary key of the instance to edit.
 * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
 * @param modalProps Properties to pass to the custom element constructor when found.
 * @param options Initialization options for the modal dialog.
 *
 * @see {@link IconEditButton} for the underlying button rendering logic.
 */
export function IconEditButtonByTagName(
    tagName: string,
    instancePk?: string | number | null,
    itemName?: string | null,
    props: IconEditButtonProps<CustomElementConstructor> = defaultIconEditButtonProps,
): SlottedTemplateResult {
    const Constructor = lookupElementConstructor(tagName);
    props = { ...defaultIconEditButtonProps, ...props };
    return IconEditButton(Constructor, instancePk, itemName, props);
}
