/**
 * @file ShadowDOM CSS for the Divider component
 */

import { css } from "lit";

export const styles = css`
    :host([orientation="vertical"]) {
        --ak-c-divider--display: inline-flex;
        --ak-c-divider--flex-direction: column;
        --ak-c-divider--content-spacing: 0.05rem;
        --ak-c-divider--height: 100%;
        --ak-c-divider--margin: 0 var(--ak-c-divider--content-spacing);
        --ak-c-divider__line--before--top: 0;
        --ak-c-divider__line--before--left: 50%;
        --ak-c-divider__line--before--width: var(--ak-c-divider--line-thickness);
        --ak-c-divider__line--before--height: 100%;
    }

    :host {
        display: var(--ak-c-divider--display);
        height: var(--ak-c-divider--height);
        margin: var(--ak-c-divider--margin);
    }

    /* Base divider container styles */
    [part="divider"] {
        align-items: center;
        display: flex;
        flex-direction: var(--ak-c-divider--flex-direction);
        width: 100%;
        height: var(--ak-c-divider--height);
    }

    [part~="line"] {
        flex-grow: 1;
        position: relative;
    }

    [part~="line"]::before {
        content: "";
        position: absolute;
        background-color: var(--ak-c-divider--color);
        left: var(--ak-c-divider__line--before--left);
        top: var(--ak-c-divider__line--before--top);
        width: var(--ak-c-divider__line--before--width);
        height: var(--ak-c-divider__line--before--height);
    }

    [part="content"] {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
    }

    [part="content"].has-content {
        padding: 0 var(--ak-c-divider--content-spacing);
    }

    :host([orientation="vertical"]) [part="content"].has-content {
        padding: var(--ak-c-divider--content-spacing) 0;
    }

    ::slotted(*) {
        color: var(--ak-c-divider--color);
    }

    :host([variant="strong"]) {
        --ak-c-divider--color: var(--ak-c-divider--strong-color);
    }

    :host([variant="subtle"]) {
        --ak-c-divider--color: var(--ak-c-divider--subtle-color);
    }
`;

export default styles;
