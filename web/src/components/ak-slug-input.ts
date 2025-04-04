import { formatAsSlug } from "@goauthentik/elements/router";

import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { HorizontalLightComponent } from "./HorizontalLightComponent";

@customElement("ak-slug-input")
export class AkSlugInput extends HorizontalLightComponent<string> {
    @property({ type: String, reflect: true })
    value = "";

    @property({ type: String })
    source = "";

    origin?: HTMLInputElement | null;

    @query("input")
    input!: HTMLInputElement;

    touched: boolean = false;

    constructor() {
        super();
        this.slugify = this.slugify.bind(this);
        this.handleTouch = this.handleTouch.bind(this);
    }

    firstUpdated() {
        this.input.addEventListener("input", this.handleTouch);
    }

    // Do not stop propagation of this event; it must be sent up the tree so that a parent
    // component, such as a custom forms manager, may receive it.
    handleTouch(ev: Event) {
        this.input.value = formatAsSlug(this.input.value);
        this.value = this.input.value;

        if (this.origin && this.origin.value === "" && this.input.value === "") {
            this.touched = false;
            return;
        }

        if (ev && ev.target && ev.target instanceof HTMLInputElement) {
            this.touched = true;
        }
    }

    slugify(ev: Event) {
        if (!(ev && ev.target && ev.target instanceof HTMLInputElement)) {
            return;
        }

        // Reset 'touched' status if the slug & target have been reset
        if (ev.target.value === "" && this.input.value === "") {
            this.touched = false;
        }

        // Don't proceed if the user has hand-modified the slug
        if (this.touched) {
            return;
        }

        // A very primitive heuristic: if the previous iteration of the slug and the current
        // iteration are *similar enough*, set the input value. "Similar enough" here is defined as
        // "any event which adds or removes a character but leaves the rest of the slug looking like
        // the previous iteration, set it to the current iteration."

        const newSlug = formatAsSlug(ev.target.value);
        const oldSlug = this.input.value;
        const [shorter, longer] =
            newSlug.length < oldSlug.length ? [newSlug, oldSlug] : [oldSlug, newSlug];

        if (longer.substring(0, shorter.length) !== shorter) {
            return;
        }

        // The browser, as a security measure, sets the originating HTML object to be the
        // target; developers cannot change it. In order to provide a meaningful value
        // to listeners, both the name and value of the host must match those of the target
        // input. The name is already handled since it's both required and automatically
        // forwarded to our templated input, but the value must also be set.

        this.value = this.input.value = newSlug;
        this.dispatchEvent(
            new Event("input", {
                bubbles: true,
                cancelable: true,
            }),
        );
    }

    connectedCallback() {
        super.connectedCallback();

        // Set up listener on source element, so we can slugify the content.
        setTimeout(() => {
            if (this.source) {
                const rootNode = this.getRootNode();
                if (rootNode instanceof ShadowRoot || rootNode instanceof Document) {
                    this.origin = rootNode.querySelector(this.source);
                }
                if (this.origin) {
                    this.origin.addEventListener("input", this.slugify);
                }
            }
        }, 0);
    }

    disconnectedCallback() {
        if (this.origin) {
            this.origin.removeEventListener("input", this.slugify);
        }
        super.disconnectedCallback();
    }

    renderControl() {
        return html`<input
            type="text"
            value=${ifDefined(this.value)}
            class="pf-c-form-control"
            ?required=${this.required}
        />`;
    }
}

export default AkSlugInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-slug-input": AkSlugInput;
    }
}
