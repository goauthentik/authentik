import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { modalInvoker, ModelFormLikeConstructor } from "#elements/dialogs/directives";
import type { DialogInit, TransclusionElementConstructor } from "#elements/dialogs/shared";
import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

/**
 * A helper function to render a button that opens a modal for editing an existing model instance.
 *
 * @param factory A custom element constructor or a function that returns a template result.
 * @param instancePk The primary key of the instance to edit.
 * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
 * @param modalProps Properties to pass to the custom element constructor when the factory is a constructor.
 * @param options Initialization options for the modal dialog.
 */
export function IconEditButton<T extends TransclusionElementConstructor>(
    factory: T,
    instancePk?: string | number | null,
    itemName?: string | null,
    modalProps?: T extends TransclusionElementConstructor
        ? LitPropertyRecord<InstanceType<T>>
        : null,
    options?: DialogInit,
): SlottedTemplateResult {
    const noun = (factory as TransclusionElementConstructor).verboseName ?? msg("Entity");
    const label = itemName
        ? msg(str`Edit "${itemName}" ${noun}`, {
              id: "entity.edit.named",
          })
        : msg(str`Edit ${noun}`, {
              id: "entity.edit",
          });

    const props: LitPropertyRecord<ModelFormLikeConstructor> = { ...modalProps, instancePk };

    return html`<button
        type="button"
        aria-label=${label}
        class="pf-c-button pf-m-plain"
        ${modalInvoker(factory, props as unknown as undefined, options)}
    >
        <pf-tooltip position="top" content=${msg("Edit")}>
            <i aria-hidden="true" class="fas fa-edit"></i>
        </pf-tooltip>
    </button>`;
}
