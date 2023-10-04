import { convertToSlug } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";

import { TemplateResult, html, nothing } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-slug-input")
export class AkSlugInput extends AKElement {
    // Render into the lightDOM. This effectively erases the shadowDOM nature of this component, but
    // we're not actually using that and, for the meantime, we need the form handlers to be able to
    // find the children of this component.
    //
    // TODO: This abstraction is wrong; it's putting *more* layers in as a way of managing the
    // visual clutter and legibility issues of ak-form-elemental-horizontal and patternfly in
    // general.
    protected createRenderRoot() {
        return this;
    }

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label = "";

    @property({ type: String, reflect: true })
    value = "";

    @property({ type: Boolean })
    required = false;

    @property({ type: String })
    help = "";

    @property({ type: Boolean })
    hidden = false;

    @property({ type: Object })
    bighelp!: TemplateResult | TemplateResult[];

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

    renderHelp() {
        return [
            this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing,
            this.bighelp ? this.bighelp : nothing,
        ];
    }

    // Do not stop propagation of this event; it must be sent up the tree so that a parent
    // component, such as a custom forms manager, may receive it.
    handleTouch(ev: Event) {
        this.input.value = convertToSlug(this.input.value);
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

        const newSlug = convertToSlug(ev.target.value);
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

    render() {
        return html`<ak-form-element-horizontal
            label=${this.label}
            ?required=${this.required}
            ?hidden=${this.hidden}
            name=${this.name}
        >
            <input
                type="text"
                value=${ifDefined(this.value)}
                class="pf-c-form-control"
                ?required=${this.required}
            />
            ${this.renderHelp()}
        </ak-form-element-horizontal> `;
    }
}

export default AkSlugInput;
