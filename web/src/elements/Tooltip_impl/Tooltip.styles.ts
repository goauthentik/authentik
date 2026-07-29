/**
 * @file ShadowDOM CSS for the Tooltip component
 */

import { css } from "lit";

/* This file is not automatically derived via WCCSS. It has been heavily modified to support using
 * `floating` and the `<dialog>` component.
 */

export const styles = css`
    @media (prefers-reduced-motion) {
        :host {
            --ak-c-tooltip--ShowDelay: 1s;
            --ak-c-tooltip--HideDelay: 1s;
            --ak-c-tooltip--TimingFunction: linear;
            --ak-c-tooltip--TransitionDuration: 0s;
        }
    }

    [part="tooltip"] {
        font-family: var(--ak-c-tooltip--FontFamily);
        max-width: var(--ak-c-tooltip--MaxWidth);
        box-shadow: var(--ak-c-tooltip--BoxShadow);
        border: 0;
        margin: 0;
        opacity: 0;
        padding: 0;
        position: absolute;
        white-space: nowrap;
        transition:
            display var(--ak-c-tooltip--TransitionDuration) var(--ak-c-tooltip--TimingFunction)
                allow-discrete,
            overlay var(--ak-c-tooltip--TransitionDuration) var(--ak-c-tooltip--TimingFunction)
                allow-discrete;
        animation: close var(--ak-c-tooltip--TransitionDuration) var(--ak-c-tooltip--TimingFunction)
            forwards;
    }

    [part="tooltip"][open] {
        animation: open var(--ak-c-tooltip--TransitionDuration) var(--ak-c-tooltip--TimingFunction)
            forwards;
    }

    [part="arrow"] {
        position: absolute;
        top: var(--ak-c-tooltip__arrow--Top, auto);
        right: var(--ak-c-tooltip__arrow--Right, auto);
        bottom: var(--ak-c-tooltip__arrow--Bottom, auto);
        left: var(--ak-c-tooltip__arrow--Left, auto);
        width: var(--ak-c-tooltip__arrow--Width);
        height: var(--ak-c-tooltip__arrow--Height);
        pointer-events: none;
        background-color: var(--ak-c-tooltip__arrow--BackgroundColor);
        box-shadow: var(--ak-c-tooltip__arrow--BoxShadow);
        transform: translateX(var(--ak-c-tooltip__arrow--TranslateX, 0))
            translateY(var(--ak-c-tooltip__arrow--TranslateY, 0))
            rotate(var(--ak-c-tooltip__arrow--Rotate, 0));
    }

    .m-top,
    .m-top-start,
    .m-top-end {
        --ak-c-tooltip__arrow--Bottom: var(--ak-c-tooltip--m-top--Bottom, 0);
        --ak-c-tooltip__arrow--Left: var(--ak-c-tooltip--m-top--Left, 50%);
        --ak-c-tooltip__arrow--TranslateX: var(--ak-c-tooltip__arrow--m-top--TranslateX);
        --ak-c-tooltip__arrow--TranslateY: var(--ak-c-tooltip__arrow--m-top--TranslateY);
        --ak-c-tooltip__arrow--Rotate: var(--ak-c-tooltip__arrow--m-top--Rotate);
    }

    .m-bottom,
    .m-bottom-start,
    .m-bottom-end {
        --ak-c-tooltip__arrow--Top: var(--ak-c-tooltip--m-bottom--Top, 0);
        --ak-c-tooltip__arrow--Left: var(--ak-c-tooltip--m-bottom--Left, 50%);
        --ak-c-tooltip__arrow--TranslateX: var(--ak-c-tooltip__arrow--m-bottom--TranslateX);
        --ak-c-tooltip__arrow--TranslateY: var(--ak-c-tooltip__arrow--m-bottom--TranslateY);
        --ak-c-tooltip__arrow--Rotate: var(--ak-c-tooltip__arrow--m-bottom--Rotate);
    }

    .m-left,
    .m-left-start,
    .m-left-end {
        --ak-c-tooltip__arrow--Top: var(--ak-c-tooltip--m-left--Top, 50%);
        --ak-c-tooltip__arrow--Right: var(--ak-c-tooltip--m-left--Right, 0);
        --ak-c-tooltip__arrow--TranslateX: var(--ak-c-tooltip__arrow--m-left--TranslateX);
        --ak-c-tooltip__arrow--TranslateY: var(--ak-c-tooltip__arrow--m-left--TranslateY);
        --ak-c-tooltip__arrow--Rotate: var(--ak-c-tooltip__arrow--m-left--Rotate);
    }

    .m-right,
    .m-right-start,
    .m-right-end {
        --ak-c-tooltip__arrow--Top: var(--ak-c-tooltip--m-right--Top, 50%);
        --ak-c-tooltip__arrow--Left: var(--ak-c-tooltip--m-right--Left, 0);
        --ak-c-tooltip__arrow--TranslateX: var(--ak-c-tooltip__arrow--m-right--TranslateX);
        --ak-c-tooltip__arrow--TranslateY: var(--ak-c-tooltip__arrow--m-right--TranslateY);
        --ak-c-tooltip__arrow--Rotate: var(--ak-c-tooltip__arrow--m-right--Rotate);
    }

    .m-left-start,
    .m-right-start {
        --ak-c-tooltip__arrow--Top: 0;
        --ak-c-tooltip__arrow--TranslateY: var(--ak-c-tooltip__arrow--m-top--TranslateY);
    }

    .m-left-end,
    .m-right-end {
        --ak-c-tooltip__arrow--Top: auto;
        --ak-c-tooltip__arrow--Bottom: 0;
    }

    .m-top-start,
    .m-bottom-start {
        --ak-c-tooltip__arrow--Left: 0;
        --ak-c-tooltip__arrow--TranslateX: var(--ak-c-tooltip__arrow--m-left--TranslateX);
    }

    .m-top-end,
    .m-bottom-end {
        --ak-c-tooltip__arrow--Right: 0;
        --ak-c-tooltip__arrow--Left: auto;
    }

    [part="content"] {
        position: relative;
        padding-block-start: var(--ak-c-tooltip__content--PaddingTop);
        padding-block-end: var(--ak-c-tooltip__content--PaddingBottom);
        padding-inline-start: var(--ak-c-tooltip__content--PaddingLeft);
        padding-inline-end: var(--ak-c-tooltip__content--PaddingRight);
        background: var(--ak-c-tooltip__content--BackgroundColor);
        font-size: var(--ak-c-tooltip__content--FontSize);
        color: var(--ak-c-tooltip__content--Color);
        text-align: center;
        overflow-wrap: anywhere;
    }

    :host([left-aligned]) [part="content"] {
        text-align: start;
    }

    @keyframes open {
        from {
            opacity: 0;
        }

        to {
            opacity: 1;
        }
    }

    @keyframes close {
        from {
            opacity: 1;
        }

        to {
            opacity: 0;
        }
    }
`;

export default styles;
