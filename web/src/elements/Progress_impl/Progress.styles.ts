import { css } from "lit";

export const styles = css`
    :host(:not([hidden])) {
        display: block;
    }

    [part="main"] {
        display: grid;
        grid-template-rows: 1fr auto;
        grid-template-columns: auto auto;
        gap: var(--ak-c-progress--GridGap);
        align-items: end;
    }

    :host([size="sm"]) {
        --ak-c-progress__bar--Height: var(--ak-c-progress--m-sm__bar--Height);
    }

    :host([size="lg"]) {
        --ak-c-progress__bar--Height: var(--ak-c-progress--m-lg__bar--Height);
        --ak-c-progress__indicator--Height: var(--ak-c-progress--m-lg__bar--Height);
    }

    :host([variant="inside"]) [part="indicator"] {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: var(--ak-c-progress--m-inside__indicator--MinWidth);
    }

    :host([variant="inside"]) [part="measure"] {
        font-size: var(--ak-c-progress--m-inside__measure--FontSize);
        color: var(--ak-c-progress--m-inside__measure--Color);
        text-align: center;
    }

    :host([size="sm"]) [part="measure"] {
        font-size: var(--ak-c-progress--m-sm__measure--FontSize);
    }

    :host([variant="outside"]) [part="main"] {
        grid-template-columns: 1fr fit-content(50%);
    }

    :host([variant="outside"]) [part="measure"] {
        display: inline-block;
        font-size: var(--ak-c-progress--m-outside__measure--FontSize);
    }

    :host([variant="outside"]) [part="status"] {
        grid-row: 2/3;
        grid-column: 2/3;
        align-self: center;
    }

    :host([variant="outside"]) [part="bar"],
    :host([variant="outside"]) [part="indicator"] {
        grid-column: 1/2;
    }

    :host([severity="success"]) {
        --ak-c-progress__bar--before--BackgroundColor: var(
            --ak-c-progress--m-success__bar--BackgroundColor
        );
        --ak-c-progress--m-inside__measure--Color: var(
            --ak-c-progress--m-success--m-inside__measure--Color
        );
        --ak-c-progress__indicator--BackgroundColor: var(
            --ak-c-progress--m-success__bar--BackgroundColor
        );
    }

    :host([severity="warning"]) {
        --ak-c-progress__bar--before--BackgroundColor: var(
            --ak-c-progress--m-warning__bar--BackgroundColor
        );
        --ak-c-progress--m-inside__measure--Color: var(
            --ak-c-progress--m-warning--m-inside__measure--Color
        );
        --ak-c-progress__indicator--BackgroundColor: var(
            --ak-c-progress--m-warning__bar--BackgroundColor
        );
    }

    :host([severity="danger"]) {
        --ak-c-progress__bar--before--BackgroundColor: var(
            --ak-c-progress--m-danger__bar--BackgroundColor
        );
        --ak-c-progress__indicator--BackgroundColor: var(
            --ak-c-progress--m-danger__bar--BackgroundColor
        );
    }

    [part="indicator"] {
        position: absolute;
        height: var(--ak-c-progress__indicator--Height);
        background-color: var(--ak-c-progress__indicator--BackgroundColor);
    }

    [part="bar"] {
        position: relative;
        grid-row: 2/3;
        grid-column: 1/3;
        align-self: center;
        height: var(--ak-c-progress__bar--Height);
        background-color: var(--ak-c-progress__bar--BackgroundColor);
        overflow: hidden;
    }

    [part="status"] {
        display: flex;
        grid-row: 1/2;
        grid-column: 2/3;
        gap: var(--ak-c-progress__status--Gap);
        align-items: flex-start;
        justify-content: flex-end;
        text-align: end;
        overflow-wrap: anywhere;
    }

    [part="bar"]::before {
        top: 0;
        left: 0;
        position: absolute;
        width: 100%;
        height: 100%;
        content: "";
        background-color: var(--ak-c-progress__bar--before--BackgroundColor);
        opacity: var(--ak-c-progress__bar--before--Opacity);
    }

    :host([size="xs"]) {
        --ak-c-progress__bar--Height: var(--ak-c-progress--m-xs__bar--Height);
    }

    :host([variant="indeterminate"]) {
        --ak-c-progress--GridGap: var(--ak-c-progress--m-indeterminate--GridGap);

        margin-bottom: calc(var(--ak-c-progress__bar--Height) * -1);
        z-index: 1;
        position: relative;
    }

    :host([variant="indeterminate"]) [part="indicator"] {
        width: 100%;
        height: 100%;
        animation: indeterminate-animation 1s infinite linear;
        transform-origin: 0% 50%;
    }

    @keyframes indeterminate-animation {
        0% {
            transform: translateX(0) scaleX(0);
        }

        40% {
            transform: translateX(0) scaleX(0.4);
        }

        100% {
            transform: translateX(100%) scaleX(0.5);
        }
    }
`;

export default styles;
