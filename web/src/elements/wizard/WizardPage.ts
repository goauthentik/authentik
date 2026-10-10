import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";
import type { AKWizard } from "#elements/wizard/Wizard";

import { ConsoleLogger } from "#logger/browser";

import { msg } from "@lit/localize";
import { html, LitElement, PropertyDeclaration } from "lit";
import { property } from "lit/decorators.js";

/**
 * Callback for when the page is brought into view.
 */
export type WizardPageActiveCallback = () => void | Promise<void>;

/**
 * Callback for when the next button is pressed.
 *
 * @returns `true` if the wizard can proceed to the next page, `false` otherwise.
 */
export type WizardPageNextCallback = (event?: Event) => boolean | Promise<boolean>;

export interface WizardPageState {
    [slotName: string]: unknown;
}

export abstract class WizardPage<S = WizardPageState> extends AKElement {
    declare parentElement: AKWizard<S> | null;
    declare slot: Extract<keyof S, string>;

    protected logger = ConsoleLogger.prefix(this.localName);
    protected defaultSlot = this.ownerDocument.createElement("slot");

    /**
     * The label to display in the sidebar for this page.
     *
     * @see {@linkcode formatSidebarLabel} for a method to compute this value based on the page's content or other properties.
     */
    @property({ type: String, attribute: "headline" })
    public headline: string | null = null;

    public get host(): AKWizard<S> {
        return this.parentElement!;
    }

    /**
     * Reset the page to its initial state.
     *
     * @abstract
     */
    public reset(): void | Promise<void> {
        console.debug(`authentik/wizard ${this.localName}: reset)`);
    }

    /**
     * Called when this is the page brought into view.
     */
    public activeCallback: WizardPageActiveCallback = () => {
        this.host.valid = false;
    };

    /**
     * An overridable method to compute the sidebar label for this page.
     *
     * Override to compute a label based on the page's content or other properties.
     *
     * @returns The {@linkcode headline} to display for this page in the sidebar.
     */
    public formatSidebarLabel(): SlottedTemplateResult {
        return html`<div part="sidebar-label-headline">${this.headline ?? msg("UNNAMED")}</div>`;
    }

    /**
     * Optional override for the wizard's next-button label while this page is active.
     *
     * Return `null` (the default) to keep the wizard's default labeling
     * (Next/Finish/Create).
     */
    public formatNextLabel(): SlottedTemplateResult | null {
        return null;
    }

    /**
     * Called when the `next` button on the wizard is pressed. For forms, results in the submission
     * of the current form to the back-end before being allowed to proceed to the next page. This is
     * sub-optimal if we want to collect multiple bits of data before finishing the whole course.
     *
     * @returns `true` if the wizard can proceed to the next page, `false` otherwise.
     */
    public nextCallback: WizardPageNextCallback = () => {
        return Promise.resolve(true);
    };

    public constructor() {
        super();
        this.part.add("wizard-page");
    }

    public override requestUpdate(
        name?: PropertyKey,
        oldValue?: unknown,
        options?: PropertyDeclaration<unknown, unknown>,
    ): void {
        for (const element of this.querySelectorAll("*")) {
            if (element instanceof LitElement) {
                element.requestUpdate();
            }
        }

        return super.requestUpdate(name, oldValue, options);
    }

    protected override render(): SlottedTemplateResult {
        return this.defaultSlot;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page": WizardPage;
    }
}
