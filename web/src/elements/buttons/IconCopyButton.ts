import "#elements/Spinner";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { ClipboardItemSource, writeToClipboard } from "#common/clipboard";
import { PFSize } from "#common/enums";

import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { html } from "lit";

export interface IconCopyButtonProps {
    source: ClipboardItemSource | null | ((event: Event) => ClipboardItemData | null);
    buttonLabel?: string;
    tooltipLabel?: string;
    entityLabel?: string;
    description?: string;
}

export function IconCopyButton({
    source,
    buttonLabel = msg("Copy to clipboard"),
    tooltipLabel = buttonLabel,
    entityLabel,
    description,
}: IconCopyButtonProps): SlottedTemplateResult {
    const doCopy = (event: PointerEvent) => {
        if (typeof source !== "function") {
            return writeToClipboard(source, entityLabel, description);
        }

        const button = event.currentTarget as HTMLButtonElement;

        const spinner = button.ownerDocument.createElement("ak-spinner");
        spinner.size = PFSize.Large;

        spinner.classList.add("ak-c-button--icon__progress");
        spinner.setAttribute("aria-hidden", "true");

        button.prepend(spinner);

        return writeToClipboard(
            typeof source === "function" ? source(event) : source,
            entityLabel,
            description,
        ).finally(() => spinner.remove());
    };

    return html`<button
        class="pf-c-button pf-m-plain"
        type="button"
        @click=${doCopy}
        aria-label=${buttonLabel}
    >
        <i class="fas fa-copy" aria-hidden="true"></i>
        <pf-tooltip position="top" content=${tooltipLabel}> </pf-tooltip>
    </button>`;
}
