import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, html, LitElement } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ref, RefOrCallback } from "lit/directives/ref.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Finds the main content element within a given context.
 *
 * @param context - The element to start searching from
 * @returns The main content element, if any.
 */
export function findMainContent(context: HTMLElement): HTMLElement | null {
    const renderRoot = context instanceof LitElement ? context.renderRoot : context;

    const mainContent = renderRoot.querySelector<HTMLElement>("main,[role=main]");

    if (mainContent) {
        return mainContent;
    }

    for (const element of renderRoot.children) {
        if (!(element instanceof HTMLElement)) continue;

        if (element.role === "presentation" || element.role === "status") continue;

        if (!element.checkVisibility?.()) continue;

        if (element.inert) continue;

        if (element instanceof LitElement && element.renderRoot !== element) {
            const child = findMainContent(element);

            if (child) return child;

            continue;
        }

        return element;
    }

    return null;
}

@customElement("ak-skip-to-content")
export class AKSkipToContent extends AKElement {
    static shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };
    static styles = [
        PFBase,
        css`
            [part="show-on-focus"] {
                position: absolute !important;
                z-index: 99999;
                color: var(--ak-dark-foreground, ButtonText);
                background-color: var(--ak-accent, ButtonFace);
                font-family: var(--pf-global--FontFamily--heading--sans-serif, sans-serif);
                padding: var(--pf-global--spacer--md, 2em);
                border-radius: var(--pf-global--BorderRadius--sm, 3px);
                border-style: dotted;
                border-width: 1px;

                &:not(:focus) {
                    width: 1px !important;
                    height: 1px !important;
                    padding: 0 !important;
                    overflow: hidden !important;
                    clip: rect(1px, 1px, 1px, 1px) !important;
                    border: 0 !important;
                }
            }
        `,
    ];

    /**
     * Assign a target element to all skip to content buttons.
     *
     * @see {@linkcode AKSkipToContent.ref} for more information on Lit's ref directive.
     */
    protected static assign: RefOrCallback<Element> = (nextTarget) => {
        if (!(nextTarget instanceof HTMLElement)) return;

        const skipToContentElement = document.getElementsByTagName("ak-skip-to-content");

        for (const skipElement of skipToContentElement) {
            skipElement.targetElement = nextTarget;
        }
    };

    /**
     * Assign a target element to the skip to content button via Lit's directive system.
     *
     * ```ts
     * function render() {
     *   return html`<main ${AKSkipToContent.ref}></main>`;
     * }
     * ```
     *
     * @see {@linkcode ref} for more information on Lit's ref directive.
     */
    public static ref = ref(AKSkipToContent.assign);

    #targetElement: WeakRef<HTMLElement> | null = null;

    @property({ attribute: false })
    public get targetElement(): HTMLElement | null {
        return this.#targetElement?.deref() ?? null;
    }

    public set targetElement(nextTargetElement: HTMLElement | null | undefined) {
        const previousTarget = this.targetElement;

        if (previousTarget === nextTargetElement) return;

        if (previousTarget) {
            previousTarget.removeAttribute("tabindex");
            previousTarget.removeAttribute("data-ak-skip-to-content-target");
        }

        if (nextTargetElement) {
            this.#targetElement = new WeakRef(nextTargetElement);
            nextTargetElement.tabIndex = -1;

            nextTargetElement.setAttribute("data-ak-skip-to-content-target", "true");
        } else {
            this.#targetElement = null;
        }
    }

    public activate = () => {
        const { targetElement } = this;

        if (!targetElement) {
            console.warn(`Could not find target element for skip to content`);
            return;
        }

        targetElement.scrollIntoView();
        targetElement.focus?.();
    };

    render() {
        return html`
            <button tabindex="0" @click=${this.activate} type="button" part="show-on-focus">
                ${msg("Skip to content")}
            </button>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-skip-to-content": AKSkipToContent;
    }
}
