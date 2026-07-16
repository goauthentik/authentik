/**
 * @file ShadowDOM CSS for the Spinner component
 */

import { css } from "lit";

export const styles = css`
    :host {
        display: inline-block;
    }

    @media (prefers-reduced-motion: reduce) {
        :host {
            --ak-c-spinner--AnimationDuration: var(
                --ak-c-spinner--AnimationDuration--reduced-motion
            );
            --ak-c-spinner__path--AnimationTimingFunction: var(
                --ak-c-spinner__path--AnimationTimingFunction--reduced-motion
            );
        }
    }

    [part="spinner"] {
        width: var(--ak-c-spinner--Diameter);
        height: var(--ak-c-spinner--Diameter);
        animation: ak-c-spinner-animation-rotate calc(var(--ak-c-spinner--AnimationDuration) * 2)
            var(--ak-c-spinner--AnimationTimingFunction) infinite;
    }

    :host([inline]) {
        --ak-c-spinner--Diameter: var(--ak-c-spinner--m-inline--Diameter);
    }

    :host([size="sm"]) {
        --ak-c-spinner--Diameter: var(--ak-c-spinner--m-sm--Diameter);
    }

    :host([size="md"]) {
        --ak-c-spinner--Diameter: var(--ak-c-spinner--m-md--Diameter);
    }

    :host([size="lg"]) {
        --ak-c-spinner--Diameter: var(--ak-c-spinner--m-lg--Diameter);
    }

    :host([size="xl"]) {
        --ak-c-spinner--Diameter: var(--ak-c-spinner--m-xl--Diameter);
    }

    @keyframes ak-c-spinner-animation-rotate {
        0% {
            transform: rotate(0deg);
        }

        100% {
            transform: rotate(360deg);
        }
    }

    @keyframes ak-c-spinner-animation-dash {
        0% {
            stroke-dashoffset: 280;
            transform: rotate(0);
        }

        40% {
            stroke-dasharray: 220;
            stroke-dashoffset: 150;
        }

        100% {
            stroke-dashoffset: 280;
            transform: rotate(720deg);
        }
    }

    @media (prefers-reduced-motion: no-preference) {
        @keyframes ak-c-spinner-animation-dash {
            0% {
                stroke-dashoffset: 280;
                transform: rotate(0);
            }

            15% {
                stroke-width: calc(var(--ak-c-spinner__path--StrokeWidth) - 4);
            }

            40% {
                stroke-dasharray: 220;
                stroke-dashoffset: 150;
            }

            100% {
                stroke-dashoffset: 280;
                transform: rotate(720deg);
            }
        }
    }

    [part="circle"] {
        width: 100%;
        height: 100%;
        stroke: var(--ak-c-spinner--Color);
        stroke-dasharray: 283;
        stroke-dashoffset: 280;
        stroke-linecap: round;
        stroke-width: var(--ak-c-spinner--StrokeWidth);
        transform-origin: 50% 50%;
        animation: ak-c-spinner-animation-dash var(--ak-c-spinner--AnimationDuration)
            var(--ak-c-spinner__path--AnimationTimingFunction) infinite;
    }
`;

export default styles;
