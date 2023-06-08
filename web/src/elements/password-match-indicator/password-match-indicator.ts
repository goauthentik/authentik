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
    first = "";

    @property({ attribute: true })
    second = "";

    firstElement?: HTMLInputElement;

    secondElement?: HTMLInputElement;

    @state()
    match = false;

    constructor() {
        super();
        this.checkPasswordMatch = this.checkPasswordMatch.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        this.firstInput.addEventListener("keyup", this.checkPasswordMatch);
        this.secondInput.addEventListener("keyup", this.checkPasswordMatch);
    }

    disconnectedCallback() {
        this.secondInput.removeEventListener("keyup", this.checkPasswordMatch);
        this.firstInput.removeEventListener("keyup", this.checkPasswordMatch);
        super.disconnectedCallback();
    }

    checkPasswordMatch() {
        this.match =
            this.firstInput.value.length > 0 &&
            this.secondInput.value.length > 0 &&
            this.firstInput.value === this.secondInput.value;
    }

    get firstInput() {
        if (this.firstElement) {
            return this.firstElement;
        }
        return (this.firstElement = findInput(this.getRootNode() as Element, ELEMENT, this.first));
    }

    get secondInput() {
        if (this.secondElement) {
            return this.secondElement;
        }
        return (this.secondElement = findInput(
            this.getRootNode() as Element,
            ELEMENT,
            this.second,
        ));
    }

    render() {
        return this.match
            ? html`<i class="pf-icon pf-icon-ok pf-m-success"></i>`
            : html`<i class="pf-icon pf-icon-warning-triangle pf-m-warning"></i>`;
    }
}

export default PasswordMatchIndicator;
