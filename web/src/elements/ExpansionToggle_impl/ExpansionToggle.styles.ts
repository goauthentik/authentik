import { css } from "lit";

export const style = css`
    :host([expanded]) {
        --ak-c-expansion-toggle--Color: var(--ak-c-expansion-toggle--m-expanded--Color);
        --ak-c-expansion-toggle__icon--Rotate: var(
            --ak-c-expansion-toggle--m-expanded__icon--Rotate
        );
    }

    [part="expansion-toggle"] {
        background-color: var(--ak-c-expansion-toggle--BackgroundColor);
        padding-block-start: var(--ak-c-expansion-toggle--PaddingTop);
        padding-block-end: var(--ak-c-expansion-toggle--PaddingBottom);
        padding-inline-start: var(--ak-c-expansion-toggle--PaddingLeft);
        padding-inline-end: var(--ak-c-expansion-toggle--PaddingRight);
        display: flex;
        flex-wrap: nowrap;
        flex-direction: row;
        align-items: center;
        align-content: center;
        column-gap: var(--ak-c-expansion-toggle--ColumnGap);
    }

    [part="expansion-toggle"]:hover {
        --ak-c-expansion-toggle--Color: var(--ak-c-expansion-toggle--hover--Color);
    }

    [part="expansion-toggle"]:active {
        --ak-c-expansion-toggle--Color: var(--ak-c-expansion-toggle--active--Color);
    }

    [part="button"]:focus-visible {
        --ak-c-expansion-toggle--Color: var(--ak-c-expansion-toggle--focus--Color);

        outline: var(--ak-c-expansion-toggle--focus--OutlineWidth) solid
            var(--ak-c-expansion-toggle--focus--OutlineColor);
        outline-offset: var(--ak-c-expansion-toggle--focus--OutlineOffset);
    }

    :host([reversed]) [part="expansion-toggle"] {
        flex-direction: row-reverse;
    }

    [part="button"] {
        background-color: var(--ak-c-expansion-toggle--BackgroundColor);
        display: flex;
        flex-direction: row;
        margin-block-start: var(--ak-c-expansion-toggle--MarginTop);
        color: var(--ak-c-expansion-toggle--Color);
        border: none;
    }

    [part="icon-container"] {
        min-width: var(--ak-c-expansion-toggle__icon--MinWidth);
        color: var(--ak-c-expansion-toggle__icon--Color);
        transition: var(--ak-c-expansion-toggle__icon--Transition);
        transform: rotate(var(--ak-c-expansion-toggle__icon--Rotate));
    }

    [part="icon-container"] svg {
        width: 1em;
        height: 1em;
        vertical-align: -0.125em;
    }

    [part="label"]:not([hidden]) {
        flex-grow: 1;
    }
`;

export default style;
