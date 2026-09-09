import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { modalInvoker } from "#elements/dialogs/directives";
import type { DialogInit } from "#elements/dialogs/shared";
import type { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";

import { ObjectPermissionsPageForm } from "#admin/rbac/ObjectPermissionModal";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

/**
 * A helper function to render a button that opens a modal for editing permissions.
 *
 * @param itemName An optional name of the item to include in the button's aria-label and tooltip.
 * @param modalProps Properties to pass to the custom element constructor when the factory is a constructor.
 * @param options Initialization options for the modal dialog.
 */
export function IconPermissionButton(
    itemName?: string | null,
    modalProps?: LitPropertyRecord<ObjectPermissionsPageForm>,
    options?: DialogInit,
): SlottedTemplateResult {
    const label = itemName
        ? msg(str`Open "${itemName}" permissions`, {
              id: "permissions.modal-invoker.named",
          })
        : msg("Open permissions", {
              id: "permissions.modal-invoker",
          });

    return html`<button
        type="button"
        aria-label=${label}
        class="pf-c-button pf-m-plain"
        ${modalInvoker(ObjectPermissionsPageForm, modalProps, options)}
    >
        <pf-tooltip position="top" content=${msg("Permissions")}>
            <i aria-hidden="true" class="fas fa-lock"></i>
        </pf-tooltip>
    </button>`;
}
