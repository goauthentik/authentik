import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { modalInvoker } from "#elements/dialogs/directives";
import type { ModalTemplate } from "#elements/dialogs/invokers";
import type { DialogInit, TransclusionElementConstructor } from "#elements/dialogs/shared";
import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

export interface NewModelButtonProps {
    kind?: "primary" | "secondary" | "tertiary";
}

/**
 * A helper function to render a button that opens a **modal** for creating a new **model** instance.
 *
 * @param factory A custom element constructor or a function that returns a template result.
 * @param buttonProps Properties to customize the appearance of the button.
 * @param modalProps Properties to pass to the custom element constructor when the factory is a constructor.
 * @param options Initialization options for the modal dialog.
 */
export function ModalInvokerButton<T extends ModalTemplate | TransclusionElementConstructor>(
    factory: T,
    modalProps?: T extends TransclusionElementConstructor
        ? LitPropertyRecord<InstanceType<T>> | null
        : null,
    buttonProps?: NewModelButtonProps | null,
    options?: DialogInit,
): SlottedTemplateResult {
    const { kind = "primary" } = buttonProps ?? {};

    const { verboseName, createLabel = msg("New") } = factory as TransclusionElementConstructor;
    const label = verboseName
        ? msg(str`${createLabel} ${verboseName}`, {
              id: "invoker.label.modifier-noun",
          })
        : createLabel;

    return html`<button
        class="pf-c-button pf-m-${kind}"
        ${modalInvoker(factory, modalProps, options)}
    >
        ${label}
    </button>`;
}
