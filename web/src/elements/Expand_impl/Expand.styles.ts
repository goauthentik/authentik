import { css } from "lit";

export const styles = css`
    :host([expanded]) {
        --ak-c-expand__toggle--Color: var(--ak-c-expand__toggle--m-expanded--Color);
    }

    [part="toggle"]:hover,
    [part="toggle-text"]:hover {
        --ak-c-expand__toggle--Color: var(--ak-c-expand__toggle--hover--Color);
    }

    [part="toggle"]:active,
    [part="toggle-text"]:active {
        --ak-c-expand__toggle--Color: var(--ak-c-expand__toggle--active--Color);
    }

    [part="toggle"]:focus,
    [part="toggle-text"]:focus {
        --ak-c-expand__toggle--Color: var(--ak-c-expand__toggle--focus--Color);
    }

    [part="toggle"],
    [part="toggle-text"] {
        color: var(--ak-c-expand__toggle--Color);
        background-color: var(--ak-c-expand__toggle--BackgroundColor);
        border: none;
    }

    [part="content"] {
        max-width: var(--ak-c-expand__content--MaxWidth);
        padding-block-end: var(--ak-c-expand__content--PaddingBottom);
        padding-inline-start: var(--ak-c-expand__content--PaddingLeft);
        padding-inline-end: var(--ak-c-expand__content--PaddingRight);
        margin-block-start: var(--ak-c-expand__content--MarginTop);
    }
`;

export default styles;
