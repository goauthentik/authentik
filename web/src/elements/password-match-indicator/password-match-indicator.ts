import { AKElement } from "@goauthentik/elements/Base";

import { css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import findInput from "../password-strength-indicator/findInput.js";

/**
 * A simple display showing if the passwords match. This element is extremely fragile and
 * role-specific, depending as it does on the token string '_repeat' inside the selector.
 */

const ELEMENT = "ak-password-match-indicator";

@customElement(ELEMENT)
export class PasswordMatchIndicator extends AKElement {
    static styles = [
        PFBase,
        css`
            :host {
                display: grid;
                place-items: center center;
            }
        `,
    ];

    /**
     * The input element to observe. Attaching this to anything other than an HTMLInputElement will
     * throw an exception.
     */
    @property({ attribute: true })
    src = "";

    sourceInput?: HTMLInputElement;
    otherInput?: HTMLInputElement;

    @state()
    match = false;

    constructor() {
        super();
        this.checkPasswordMatch = this.checkPasswordMatch.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        this.input.addEventListener("keyup", this.checkPasswordMatch);
        this.other.addEventListener("keyup", this.checkPasswordMatch);
    }

    disconnectedCallback() {
        this.other.removeEventListener("keyup", this.checkPasswordMatch);
        this.input.removeEventListener("keyup", this.checkPasswordMatch);
        super.disconnectedCallback();
    }

    checkPasswordMatch() {
        this.match =
            this.input.value.length > 0 &&
            this.other.value.length > 0 &&
            this.input.value === this.other.value;
    }

    get input() {
        if (this.sourceInput) {
            return this.sourceInput;
        }
        return (this.sourceInput = findInput(this.getRootNode() as Element, ELEMENT, this.src));
    }

    get other() {
        if (this.otherInput) {
            return this.otherInput;
        }
        return (this.otherInput = findInput(
            this.getRootNode() as Element,
            ELEMENT,
            this.src.replace(/_repeat/, ""),
        ));
    }

    render() {
        return this.match
            ? html`<i class="pf-icon pf-icon-ok pf-m-success"></i>`
            : html`<i class="pf-icon pf-icon-warning-triangle pf-m-warning"></i>`;
    }
}

export default PasswordMatchIndicator;
