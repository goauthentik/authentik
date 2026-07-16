/**
 * @file ShadowDOM CSS for the ToggleGroup component
 */

import { css } from "lit";

export const styles = css`
    :host([compact]) {
        --pf-c-toggle-group__button--PaddingTop: var(
            --pf-c-toggle-group--m-compact__button--PaddingTop
        );
        --pf-c-toggle-group__button--PaddingRight: var(
            --pf-c-toggle-group--m-compact__button--PaddingRight
        );
        --pf-c-toggle-group__button--PaddingBottom: var(
            --pf-c-toggle-group--m-compact__button--PaddingBottom
        );
        --pf-c-toggle-group__button--PaddingLeft: var(
            --pf-c-toggle-group--m-compact__button--PaddingLeft
        );
        --pf-c-toggle-group__button--FontSize: var(
            --pf-c-toggle-group--m-compact__button--FontSize
        );
    }

    [part="toggle-group"] {
        justify-content: center;
        display: flex;
    }

    [part="item"] + [part="item"] {
        margin-left: var(--pf-c-toggle-group__item--item--MarginLeft);
    }

    [part="item"]:first-child [part~="button"],
    [part="item"]:first-child [part~="button"]::before {
        border-top-left-radius: var(
            --pf-c-toggle-group__item--first-child__button--BorderTopLeftRadius
        );
        border-bottom-left-radius: var(
            --pf-c-toggle-group__item--first-child__button--BorderBottomLeftRadius
        );
    }

    [part="item"]:last-child [part~="button"],
    [part="item"]:last-child [part~="button"]::before {
        border-top-right-radius: var(
            --pf-c-toggle-group__item--last-child__button--BorderTopRightRadius
        );
        border-bottom-right-radius: var(
            --pf-c-toggle-group__item--last-child__button--BorderBottomRightRadius
        );
    }

    [part~="button"] {
        position: relative;
        z-index: var(--pf-c-toggle-group__button--ZIndex);
        display: inline-flex;
        padding: var(--pf-c-toggle-group__button--PaddingTop)
            var(--pf-c-toggle-group__button--PaddingRight)
            var(--pf-c-toggle-group__button--PaddingBottom)
            var(--pf-c-toggle-group__button--PaddingLeft);
        font-size: var(--pf-c-toggle-group__button--FontSize);
        line-height: var(--pf-c-toggle-group__button--LineHeight);
        color: var(--pf-c-toggle-group__button--Color);
        background-color: var(--pf-c-toggle-group__button--BackgroundColor);
        border: 0;
    }

    [part~="button"]::before {
        position: absolute;
        inset-block-start: 0;
        inset-block-end: 0;
        inset-inline-start: 0;
        inset-inline-end: 0;
        pointer-events: none;
        content: "";
        border: var(--pf-c-toggle-group__button--before--BorderWidth) solid
            var(--pf-c-toggle-group__button--before--BorderColor);
    }

    [part~="button"]:hover {
        --pf-c-toggle-group__button--BackgroundColor: var(
            --pf-c-toggle-group__button--hover--BackgroundColor
        );
        --pf-c-toggle-group__button--ZIndex: var(--pf-c-toggle-group__button--hover--ZIndex);
        --pf-c-toggle-group__button--before--BorderColor: var(
            --pf-c-toggle-group__button--hover--before--BorderColor
        );
        text-decoration: none;
    }

    [part~="button"]:focus {
        --pf-c-toggle-group__button--BackgroundColor: var(
            --pf-c-toggle-group__button--focus--BackgroundColor
        );
        --pf-c-toggle-group__button--ZIndex: var(--pf-c-toggle-group__button--focus--ZIndex);
        --pf-c-toggle-group__button--before--BorderColor: var(
            --pf-c-toggle-group__button--focus--before--BorderColor
        );
    }

    [part~="button"][part~="selected"] {
        --pf-c-toggle-group__button--BackgroundColor: var(
            --pf-c-toggle-group__button--m-selected--BackgroundColor
        );
        --pf-c-toggle-group__button--ZIndex: var(--pf-c-toggle-group__button--m-selected--ZIndex);
        --pf-c-toggle-group__button--before--BorderColor: var(
            --pf-c-toggle-group__button--m-selected--before--BorderColor
        );
    }

    [part~="button"]:disabled,
    [part~="button"][part~="disabled"] {
        --pf-c-toggle-group__button--BackgroundColor: var(
            --pf-c-toggle-group__button--disabled--BackgroundColor
        );
        --pf-c-toggle-group__button--Color: var(--pf-c-toggle-group__button--disabled--Color);
        pointer-events: none;
    }

    [part="icon"] + [part="label"],
    [part="label"] + [part="icon"] {
        margin-left: var(--pf-c-toggle-group__icon--text--MarginLeft);
    }
`;

export default styles;
