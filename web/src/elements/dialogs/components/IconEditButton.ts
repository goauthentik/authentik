import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { modalInvoker, ModelFormLikeConstructor } from "#elements/dialogs/directives";
import type {
    IconEditButtonOptions,
    NamedEntityElementConstructor,
    SplitIconName,
} from "#elements/dialogs/shared";
import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

const isSplitIconName = (v: unknown): v is SplitIconName =>
    typeof v === "object" && v !== null && ("name" in v || "ariaName" in v);

const labelMaker = (noun: string, label?: string | null) =>
    label
        ? msg(str`Edit "${label}" ${noun}`, {
              id: "entity.edit.named",
          })
        : msg(str`Edit ${noun}`, {
              id: "entity.edit",
          });

export const defaultIconEditOptions = { iconName: "fa-edit" };

/**
 * A helper function to render a button that opens a modal for editing an existing model instance.
 *
 * @param factory A custom element constructor or a function that returns a template result.
 * @param instancePk The primary key of the instance to edit.
 * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
 * @param options { @param modalProps: Properties to pass to the custom element constructor when the
 *   factory is a constructor. @param dialogOptions: Initialization options for the modal dialog.
 *   @param iconName: The icon to show. }
 */
export function IconEditButton<T extends NamedEntityElementConstructor>(
    factory: T,
    instancePk: string | number | null = null,
    itemName: string | SplitIconName | null = null,
    options: IconEditButtonOptions<T> = defaultIconEditOptions,
): SlottedTemplateResult {
    options = { ...defaultIconEditOptions, ...options };
    const noun = (factory as NamedEntityElementConstructor).verboseName ?? msg("Object");
    const labels = isSplitIconName(itemName)
        ? [itemName.ariaName, itemName.name]
        : [itemName, itemName];
    const [ariaText, label] = labels.map((s) => labelMaker(noun, s));
    const { modalProps, dialogOptions, iconName } = options;

    const props: LitPropertyRecord<ModelFormLikeConstructor> = { ...modalProps, instancePk };

    return html`<button
        type="button"
        aria-label=${ariaText}
        class="pf-c-button pf-m-plain"
        ${modalInvoker(factory, props as unknown as undefined, dialogOptions)}
    >
        <pf-tooltip position="top" content=${label}>
            <i aria-hidden="true" class="fas ${iconName}"></i>
        </pf-tooltip>
    </button>`;
}
