import "#elements/commands/ak-command-palette-modal";

import HostStyles from "./ak-command-palette.css";

import { AKElement } from "#elements/Base";
import { AKCommandPaletteModal } from "#elements/commands/ak-command-palette-modal";
import { listen } from "#elements/decorators/listen";

import { ConsoleLogger, Logger } from "#logger/browser";

import { customElement } from "lit/decorators.js";

@customElement("ak-command-palette")
export class AKCommandPalette extends AKElement {
    public static hostStyles = [HostStyles];

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    protected logger: Logger;

    public readonly dialog: HTMLDialogElement;
    public readonly modal: AKCommandPaletteModal;
    public readonly defaultSlot: HTMLSlotElement;

    constructor() {
        super();

        this.logger = ConsoleLogger.prefix(this.tagName.toLowerCase());

        this.dialog = this.ownerDocument.createElement("dialog");
        this.modal = this.ownerDocument.createElement("ak-command-palette-modal");
        this.defaultSlot = this.ownerDocument.createElement("slot");

        this.dialog.appendChild(this.modal);
        this.dialog.appendChild(this.defaultSlot);
    }

    @listen("keydown", { passive: false, capture: true })
    protected keydownListener = (event: KeyboardEvent) => {
        if (event.key !== "k" || (!event.metaKey && !event.ctrlKey)) {
            return;
        }

        event.preventDefault();

        this.logger.info("Toggling command palette");

        const open = this.modal.open;

        if (!open && event.shiftKey) {
            this.modal.value = this.modal.actionNamespaceSymbol;
        }

        this.modal.open = !open;
    };

    public showListener = (): void => {
        this.modal.open = true;
    };

    protected override render() {
        return this.dialog;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-command-palette": AKCommandPalette;
    }
}
