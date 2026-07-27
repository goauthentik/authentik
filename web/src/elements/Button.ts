/**
 * @file Barrel file and default registry ('ak-button') for the Button component
 */

import {
    Button,
    type ButtonSeverity,
    type ButtonSize,
    type ButtonType,
    type ButtonVariant,
} from "./Button_impl/Button";
import { akButton, type ButtonProps } from "./Button_impl/Button.builder";

export { akButton, Button, ButtonProps, ButtonSeverity, ButtonSize, ButtonType, ButtonVariant };

window.customElements.define("ak-button", Button);

declare global {
    interface HTMLElementTagNameMap {
        "ak-button": Button;
    }
}
