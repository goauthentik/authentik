import { autoUpdate, computePosition, flip, hide } from "@floating-ui/dom";

import { LitElement, html, nothing, render } from "lit";
import { customElement, property } from "lit/decorators.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import { SearchSelectCloseEvent } from "./SearchSelectEvents.js";
import "./ak-search-select-menu.js";
import { type SearchSelectMenu } from "./ak-search-select-menu.js";
import type { SearchOptions } from "./types.js";

/**
 * An intermediate class to handle the menu and its position.
 *
 * It has no rendering of its own, and mostly is just a pass-through for options to the menu.
 * DOTADIW: it tracks the top-of-DOM object into which we render our menu, guaranteeing that it
 * appears above everything else, and operates the positioning control for it.
 *
 * @fires ak-search-select-close - Fired when the tethered end loses focus. Clients can do with this
 * information as they wish.
 */

@customElement("ak-search-select-menu-position")
export class SearchSelectMenuPosition extends LitElement {
    /**
     * The host to which all relevant events will be routed.  Useful for managing floating / tethered
     * components.
     *
     * @prop
     */
    @property({ type: Object, attribute: false })
    host!: HTMLElement;

    /**
     * The host element which will be our reference point for rendering.
     *
     * @prop
     */
    @property({ type: Object, attribute: false })
    anchor!: HTMLElement;

    /**
     * Passthrough of the options that we'll be rendering.
     *
     * @prop
     */
    @property({ type: Array, attribute: false })
    options: SearchOptions = [];

    /**
     * Passthrough of the current value
     *
     * @prop
     */
    @property()
    value?: string;

    /**
     * If undefined, there will be no empty option shown
     *
     * @attr
     */
    @property()
    emptyOption?: string;

    /**
     * If undefined, there will be no empty option shown
     *
     * @attr
     */
    @property({ type: Boolean, reflect: true })
    hidden = false;

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

    /**
     *Communicates forward with the menu to detect when the tether has lost focus
     */
    menuRef: Ref<SearchSelectMenu> = createRef();

    connectedCallback() {
        super.connectedCallback();
        this.dropdownContainer = document.createElement("div");
        this.dropdownContainer.dataset["managedBy"] = "ak-search-select";
        if (this.name) {
            this.dropdownContainer.dataset["managedFor"] = this.name;
        }
        document.body.append(this.dropdownContainer);
        if (!this.host) {
            throw new Error("Tether entrance initialized incorrectly: missing host");
        }
        this.connected = true;
    }

    disconnectedCallback(): void {
        this.connected = false;
        this.dropdownContainer?.remove();
        this.cleanup?.();
        super.disconnectedCallback();
    }

    setPosition() {
        if (!(this.anchor && this.dropdownContainer)) {
            throw new Error(
                "Tether entrance initialized incorrectly: missing anchor or tether destination",
            );
        }

        this.cleanup = autoUpdate(this.anchor, this.dropdownContainer, async () => {
            const { middlewareData, x, y } = await computePosition(
                this.anchor,
                this.dropdownContainer,
                {
                    placement: "bottom-start",
                    strategy: "fixed",
                    middleware: [flip(), hide()],
                },
            );

            if (middlewareData.hide?.referenceHidden) {
                this.hidden = true;
                return;
            }

            Object.assign(this.dropdownContainer.style, {
                position: "fixed",
                top: 0,
                left: 0,
                transform: `translate(${x}px, ${y}px)`,
            });
        });
    }

    updated() {
        if (!this.hidden) {
            this.setPosition();
        }
    }

    hasFocus() {
        return (
            this.menuRef.value &&
            (this.menuRef.value === document.activeElement ||
                this.menuRef.value.renderRoot.contains(document.activeElement))
        );
    }

    onFocusOut() {
        this.host.dispatchEvent(new SearchSelectCloseEvent());
    }

    render() {
        render(
            html`<ak-search-select-menu
                .options=${this.options}
                .value=${this.value}
                .host=${this.host}
                .emptyOption=${this.emptyOption}
                @focusout=${this.onFocusOut}
                ?hidden=${this.hidden}
                ${ref(this.menuRef)}
            ></ak-search-select-menu>`,
            this.dropdownContainer,
        );
        // This is a dummy object that just has to exist to be the communications channel between
        // the tethered object and its anchor.
        return nothing;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-search-select-menu-position": SearchSelectMenuPosition;
    }
}
