import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import { modalInvoker } from "#elements/dialogs/directives";
import type { ModalTemplate } from "#elements/dialogs/invokers";
import {
    type DialogInit,
    formatCreateLabel,
    type NamedEntityElementConstructor,
} from "#elements/dialogs/shared";
import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { html } from "lit-html";

export interface NewModelButtonProps {
    kind?: "primary" | "secondary" | "tertiary";
}

/**
 * A helper function to render a button that opens a **modal** for creating a new **model**
 * instance.
 *
 * @param factory A custom element constructor or a function that returns a template result.
 * @param buttonProps Properties to customize the appearance of the button.
 * @param modalProps Properties to pass to the custom element constructor when the factory is a
 *   constructor.
 * @param options Initialization options for the modal dialog.
 */
export function ModalInvokerButton<T extends ModalTemplate | NamedEntityElementConstructor>(
    factory: T,
    modalProps?: T extends NamedEntityElementConstructor
        ? LitPropertyRecord<InstanceType<T>> | null
        : null,
    buttonProps?: NewModelButtonProps | null,
    options?: DialogInit,
): SlottedTemplateResult {
    const { kind = "primary" } = buttonProps ?? {};

    const label = formatCreateLabel(factory as NamedEntityElementConstructor);

    return html`<button
        class="pf-c-button pf-m-${kind}"
        ${modalInvoker(factory, modalProps, options)}
    >
        ${label}
    </button>`;
}
