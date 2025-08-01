import { HorizontalLightComponent } from "./HorizontalLightComponent.js";

import { kebabCase } from "change-case";

import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const slugify = (s: string) => kebabCase(s, { suffixCharacters: "-" });

/**
 * @element ak-slug-input
 * @class AkSlugInput
 *
 * A wrapper around `ak-form-element-horizontal` and a text input control that listens for input on
 * a peer text input control and automatically mirrors that control's value, transforming the value
 * into a slug and displaying it separately.
 *
 * If the user manually changes the slug, mirroring and transformation stop. If, after that, both
 * fields are cleared manually, mirroring and transformation resume.
 *
 * ## Limitations:
 *
 * Both the source text field and the slug field must be rendered in the same render pass (i.e.,
 * part of the same singular call to a `render` function) so that the slug field can find its
 * source.
 *
 * For the same reason, both the source text field and the slug field must share the same immediate
 * parent DOM object.
 *
 * Since we expect the source text field and the slug to be part of the same form and rendered not
 * just in the same form but in the same form group, these are not considered burdensome
 * restrictions.
 */
@customElement("ak-slug-input")
export class AkSlugInput extends HorizontalLightComponent<string> {
    /**
     * A selector indicating the source text input control. Must be unique within the whole DOM
     * context of the slug and source controls. The most common use in authentik is the default:
     * slugifying the "name" of something.
     */
    @property({ type: String })
    public source = "[name='name']";

    @property({ type: String, reflect: true })
    public value = "";

    @query("input")
    private input!: HTMLInputElement;

    #origin?: HTMLInputElement | null;

    #touched: boolean = false;

    // Do not stop propagation of this event; it must be sent up the tree so that a parent
    // component, such as a custom forms manager, may receive it.
    #touchListener = (ev: Event) => {
        this.value = this.input.value = slugify(this.input.value);

        // Reset 'touched' status if the slug & target have been reset
        if (this.#origin && this.#origin.value === "" && this.input.value === "") {
            this.#touched = false;
            return;
        }

        if (ev && ev.target && ev.target instanceof HTMLInputElement) {
            this.#touched = true;
        }
    };

    #slugify = (ev: Event) => {
        if (!(ev && ev.target && ev.target instanceof HTMLInputElement)) {
            return;
        }

        // Reset 'touched' status if the slug & target have been reset
        if (ev.target.value === "" && this.input.value === "") {
            this.#touched = false;
        }

        // Don't proceed if the user has hand-modified the slug. (Note the order of statements: if
        // the user hand modified the slug to be empty as part of resetting the slug/source
        // relationship, that's a "not-touched" condition and falls through.)
        if (this.#touched) {
            return;
        }

        // A very primitive heuristic: if the previous iteration of the slug and the current
        // iteration are *similar enough*, set the input value. "Similar enough" here is defined as
        // "any event which adds or removes a character but leaves the rest of the slug looking like
        // the previous iteration, set it to the current iteration."

        const newSlug = slugify(ev.target.value);
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
    };

    public override disconnectedCallback() {
        this.#origin?.removeEventListener("input", this.#slugify);

        super.disconnectedCallback();
    }

    public override renderControl() {
        return html`<input
            id=${ifDefined(this.fieldID)}
            @input=${this.#touchListener}
            type="text"
            value=${ifDefined(this.value)}
            class="pf-c-form-control"
            ?required=${this.required}
        />`;
    }

    public override firstUpdated() {
        if (!this.source) {
            return;
        }

        const rootNode = this.getRootNode();
        if (rootNode instanceof ShadowRoot || rootNode instanceof Document) {
            this.#origin = rootNode.querySelector(this.source);
        }
        if (this.#origin) {
            this.#origin.addEventListener("input", this.#slugify);
        }
    }
}

export default AkSlugInput;

declare global {
    interface HTMLElementTagNameMap {
        "ak-slug-input": AkSlugInput;
    }
}
