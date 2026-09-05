import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { modalInvoker, ModelFormLikeConstructor } from "#elements/dialogs/directives";
import type { DialogInit, NamedEntityElementConstructor } from "#elements/dialogs/shared";
import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

export interface IconEditButtonProps<T> {
    modalProps?: T extends NamedEntityElementConstructor
        ? LitPropertyRecord<InstanceType<T>>
        : null;
    options?: DialogInit;
    iconName?: string;
}

export const defaultIconEditButtonProps = {
    iconName: "fa-edit",
};

/**
 * A helper function to render a button that opens a modal for editing an existing model instance.
 *
 * @param factory A custom element constructor or a function that returns a template result.
 * @param instancePk The primary key of the instance to edit.
 * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
 * @param modalProps Properties to pass to the custom element constructor when the factory is a constructor.
 * @param options Initialization options for the modal dialog.
 */
export function IconEditButton<T extends NamedEntityElementConstructor>(
    factory: T,
    instancePk?: string | number | null,
    itemName?: string | null,
    props: IconEditButtonProps<T> = defaultIconEditButtonProps,
): SlottedTemplateResult {
    props = { ...defaultIconEditButtonProps, ...props };
    const noun = (factory as NamedEntityElementConstructor).verboseName ?? msg("Object");
    const { modalProps, options, iconName } = props;
    const label = itemName
        ? msg(str`Edit "${itemName}" ${noun}`, {
              id: "entity.edit.named",
          })
        : msg(str`Edit ${noun}`, {
              id: "entity.edit",
          });

    const invokerProps: LitPropertyRecord<ModelFormLikeConstructor> = { ...modalProps, instancePk };
    return html`<button
        type="button"
        aria-label=${label}
        class="pf-c-button pf-m-plain"
        ${modalInvoker(factory, invokerProps as unknown as undefined, options)}
    >
        <pf-tooltip position="top" content=${label}>
            <i aria-hidden="true" class="fas ${iconName}"></i>
        </pf-tooltip>
    </button>`;
}
