import { autoUpdate, computePosition, flip, hide } from "@floating-ui/dom";
import { randomId } from "@goauthentik/elements/utils/randomId.js";

import { LitElement, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * @class Portal
 * @element ak-portal
 *
 * An intermediate class to handle a menu and its position.
 *
 * It has no rendering of its own, and mostly is just a pass-through for options to the menu.
 * DOTADIW: it tracks the top-of-DOM object into which we render our menu, guaranteeing that it
 * appears above everything else, and operates the positioning control for it.
 *
 * - @prop anchor (HTMLElement): The component which will be visually associated with the portaled popup.
 * - @attr open (boolean): whether or not the component is visible
 * - @attr name (string): (optional) used to managed the relationship the portal mediates.
 */

export interface IPortal {
    anchor: HTMLElement;
    open: boolean;
    name?: string;
}

@customElement("ak-portal")
export class Portal extends LitElement implements IPortal {
    /**
     * The host element which will be our reference point for rendering.  Is not necessarily
     * the element that receives the events.
     *
     * @prop
     */
    @property({ type: Object, attribute: false })
    anchor!: HTMLElement;

    /**
     * Whether or not the content is visible
     *
     * @attr
     */
    @property({ type: Boolean, reflect: true })
    open = false;

    /**
     * The name; used mostly for the management layer.
     *
     * @attr
     */
    @property()
    name?: string;

    /**
     * The tether object.
     */
    dropdownContainer!: HTMLDivElement;
    public cleanup?: () => void;

    connected = false;

    content!: Element;

    connectedCallback() {
        super.connectedCallback();
        this.setAttribute("data-ouia-component-type", "ak-portal");
        this.setAttribute("data-ouia-component-id", this.getAttribute("id") || randomId());

        this.dropdownContainer = document.createElement("div");
        this.dropdownContainer.dataset.managedBy = "ak-portal";
        if (this.name) {
            this.dropdownContainer.dataset.managedFor = this.name;
        }

        document.body.append(this.dropdownContainer);

        if (!this.anchor) {
            throw new Error("Tether entrance initialized incorrectly: missing anchor");
        }

        this.connected = true;

        if (!this.firstElementChild) {
            throw new Error("No content to be portaled included in the tag");
        }
        this.content = this.firstElementChild;
    }

    disconnectedCallback(): void {
        this.connected = false;
        this.dropdownContainer?.remove();
        this.cleanup?.();
        super.disconnectedCallback();
    }

    setPosition() {
        if (!(this.anchor && this.dropdownContainer)) {
            throw new Error("Tether initialized incorrectly: missing anchor or tether destination");
        }

        this.cleanup = autoUpdate(this.anchor, this.dropdownContainer, async () => {
            const { x, y } = await computePosition(this.anchor, this.dropdownContainer, {
                placement: "bottom-start",
                strategy: "fixed",
                middleware: [flip(), hide()],
            });

            Object.assign(this.dropdownContainer.style, {
                "position": "fixed",
                "display": "block",
                "z-index": "9999",
                "top": 0,
                "left": 0,
                "transform": `translate(${x}px, ${y}px)`,
            });
        });
    }

    public override performUpdate() {
        this.removeAttribute("data-ouia-component-safe");
        super.performUpdate();
    }

    render() {
        this.dropdownContainer.appendChild(this.content);
        // This is a dummy object that just has to exist to be the communications channel between
        // the tethered object and its anchor.
        return nothing;
    }

    updated() {
        (this.content as HTMLElement).style.display = "none";
        if (this.anchor && this.dropdownContainer && this.open && !this.hidden) {
            (this.content as HTMLElement).style.display = "";
            this.setPosition();
        }
        // Testing should always check if this component is open, even if it's set safe.
        this.setAttribute("data-ouia-component-safe", "true");
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-portal": Portal;
    }
}
