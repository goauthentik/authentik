import { AKElement } from "@goauthentik/elements/Base";
import zxcvbn from "zxcvbn";

import { css, html } from "lit";
import { styleMap } from "lit-html/directives/style-map.js";
import { customElement, property, state } from "lit/decorators.js";

import findInput from "./findInput";

const styles = css`
    .password-meter-wrap {
        margin-top: 5px;
        height: 0.5em;
        background-color: #ddd;
        border-radius: 0.25em;

        overflow: hidden;
    }

    .password-meter-bar {
        width: 0;
        height: 100%;
        transition: width 400ms ease-in;
    }
`;

const LEVELS = [
    ["20%", "#dd0000"],
    ["40%", "#ff5500"],
    ["60%", "#ffff00"],
    ["80%", "#a1a841"],
    ["100%", "#339933"],
].map(([width, backgroundColor]) => ({ width, backgroundColor }));

/**
 * A simple display of the password strength.
 */

const ELEMENT = "ak-password-strength-indicator";

@customElement(ELEMENT)
export class PasswordStrengthIndicator extends AKElement {
    static styles = styles;

    /**
     * The input element to observe. Attaching this to anything other than an HTMLInputElement will
     * throw an exception.
     */
    @property({ attribute: true })
    src = "";

    sourceInput?: HTMLInputElement;

    @state()
    strength = LEVELS[0];

    constructor() {
        super();
        this.checkPasswordStrength = this.checkPasswordStrength.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        this.input.addEventListener("keyup", this.checkPasswordStrength);
    }

    disconnectedCallback() {
        this.input.removeEventListener("keyup", this.checkPasswordStrength);
        super.disconnectedCallback();
    }

    checkPasswordStrength() {
        const { score } = zxcvbn(this.input.value);
        this.strength = LEVELS[score];
    }

    get input(): HTMLInputElement {
        if (this.sourceInput) {
            return this.sourceInput;
        }
        return (this.sourceInput = findInput(this.getRootNode() as Element, ELEMENT, this.src));
    }

    render() {
        return html` <div class="password-meter-wrap">
            <div class="password-meter-bar" style=${styleMap(this.strength)}></div>
        </div>`;
    }
}

export default PasswordStrengthIndicator;
