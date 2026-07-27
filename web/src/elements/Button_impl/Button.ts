import styles from "./Button.styles";
import { buttonTemplate, linkTemplate } from "./Button.template";

import { InternalsController } from "@patternfly/pfe-core/controllers/internals-controller.js";
import { match, P } from "ts-pattern";

import { LitElement, PropertyValues } from "lit";
import { property, query } from "lit/decorators.js";

/**
 * Variant types
 */
export const buttonVariant = [
    "primary",
    "secondary",
    "tertiary",
    "control",
    "plain",
    "link",
] as const;
export type ButtonVariant = (typeof buttonVariant)[number];

/**
 * Severity levels.
 */
export const buttonSeverity = ["danger", "warning"] as const;
export type ButtonSeverity = (typeof buttonSeverity)[number];

/**
 * Optional button sizes
 */
export const buttonSize = ["sm", "md", "lg"] as const;
export type ButtonSize = (typeof buttonSize)[number];

/**
 * Button behaviors.
 */
export const buttonType = ["button", "submit", "reset"] as const;
export type ButtonType = (typeof buttonType)[number];

/**
 * @element ak-button
 *
 * @summary A button component with multiple variants, sizes, and form integration capabilities
 *
 * @attr {ButtonType} type - Button behavior: "button" (default), "submit", "reset"
 * @attr {ButtonVariant} variant - Visual variant
 *   - "primary": Filled button with strong emphasis
 *   - "secondary": Outlined button with medium emphasis
 *   - "tertiary": Subtle button with low emphasis
 *   - "control": Button used in form controls
 *   - "plain": Icon button without background/border
 *   - "link": Looks like a hyperlink
 * @attr {ButtonSeverity} severity - Severity level: "danger", "warning"
 *   - "danger": Red styling for destructive actions
 *   - "warning": Yellow styling for cautionary actions
 * @attr {ButtonSize} size - Button size: "sm", "lg"
 *   - "sm": Smaller than default. Used for compact settings.
 *   - "md": Medium (the default)
 *   - "lg": Larger than default. Used for CTAs.
 * @attr {string} name - Name attribute for the button
 * @attr {string} value - Value attribute when button is part of a form
 * @attr {string} label - Aria-accessible label for the button
 * @attr {string} href - URL to navigate to (for link variant)
 * @attr {string} target - Target attribute for link variant (e.g., "_blank")
 * @attr {boolean} disabled - Whether the button is disabled
 * @attr {boolean} block - Whether button occupies full width of container
 * @attr {boolean} inline - Whether button flows inline with text (removes host padding)
 * @attr {boolean} active - Whether button is in active state
 * @attr {boolean} expanded - Whether control variant button is in expanded state
 *
 * @fires click - Fired when button is clicked (unless disabled)
 *
 * @slot - Default slot for button content (text, icons, etc.)
 *
 * @csspart button - The button element (when not using href)
 * @csspart anchor - The anchor element (when href is provided)
 *
 */
export class Button extends LitElement {
    static override shadowRootOptions = { ...LitElement.shadowRootOptions, delegatesFocus: true };

    static readonly styles = [styles];

    static readonly formAssociated = true;

    // While it's unlikely that client code will modify these by manipulating `type` and `variant`
    // fields directly, it's still possible. Their presence triggers corresponding CSS effects, so
    // they must be monitored and reflected.
    @property({ reflect: true })
    public type?: ButtonType = "button";

    @property({ reflect: true })
    public variant: ButtonVariant = "primary";

    @property()
    public label?: string;

    @property()
    public name?: string;

    @property()
    public value?: string;

    @property()
    public href?: string;

    @property()
    public target?: string;

    @property()
    public rel?: string;

    @property()
    public download?: string;

    #internals = InternalsController.of(this);

    @property({ reflect: true, type: Boolean })
    public disabled = false;

    @query("#main")
    theButton?: HTMLButtonElement;

    get #disabled() {
        return this.matches(":disabled") || this.disabled;
    }

    private onClick = (event: MouseEvent) => {
        // Using `requestSubmit()` rather than `submit()`.  See:
        // https://github.com/WICG/webcomponents/issues/814

        // prettier-ignore
        match([this.disabled, this.type])
            .with([true, P._], () => { event.preventDefault(); })
            .with([false, "reset"], () => { this.#internals.form?.reset(); })
            .with([false, "submit"], () => { this.#internals.form?.requestSubmit(this.theButton); })
            .otherwise(() => { /* no-op */ });
    };

    formDisabledCallback(disabled: boolean) {
        if (disabled) {
            this.theButton?.setAttribute("disabled", "");
            this.setAttribute("disabled", "");
        } else {
            // Logic for when the element becomes enabled
            this.theButton?.removeAttribute("disabled");
            this.removeAttribute("disabled");
        }
    }

    constructor() {
        super();
        this.addEventListener("click", this.onClick);
    }

    public willUpdate(changed: PropertyValues<this>): void {
        super.willUpdate(changed);
        this.#internals.ariaLabel = this.label || null;
        this.#internals.ariaDisabled = String(!!this.#disabled);
    }

    public override render() {
        const { href, type, target, name, value, rel, download, onClick } = this;
        const disabled = this.#disabled;

        return this.variant === "link" && typeof href === "string"
            ? linkTemplate({ href, target, disabled, rel, download, onClick })
            : buttonTemplate({ disabled, type, name, value, onClick });
    }
}
