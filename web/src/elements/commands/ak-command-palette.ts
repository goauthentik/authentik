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

    protected activationKeys = new Set(["k", "/"]);

    constructor() {
        super();

        this.logger = ConsoleLogger.prefix(this.localName);

        this.dialog = this.ownerDocument.createElement("dialog");
        this.modal = this.ownerDocument.createElement("ak-command-palette-modal");
        this.defaultSlot = this.ownerDocument.createElement("slot");

        this.dialog.appendChild(this.modal);
        this.dialog.appendChild(this.defaultSlot);
    }

    @listen("keydown", {
        target: window,
        passive: false,
        capture: true,
    })
    protected keydownListener = (event: KeyboardEvent) => {
        if (!this.activationKeys.has(event.key) || (!event.metaKey && !event.ctrlKey)) {
            return;
        }

        event.preventDefault();

        this.logger.info("Toggling command palette");

        const open = this.modal.open;

        if (!open) {
            if (event.shiftKey) {
                this.modal.value = this.modal.actionNamespaceSymbol;
            } else if (event.key === "/") {
                this.modal.value = this.modal.searchNamespaceSymbol;
            }
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
