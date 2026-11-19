import { css } from "lit";

export const styles = css`
    :host {
        --pf-c-spinner--diameter: var(--pf-c-spinner--m-md--diameter);
        display: inline-block;
        width: var(--pf-c-spinner--diameter);
        height: var(--pf-c-spinner--diameter);
        overflow: hidden;
    }

    :host([size="sm"]) {
        --pf-c-spinner--diameter: var(--pf-c-spinner--m-sm--diameter);
    }

    :host([size="lg"]) {
        --pf-c-spinner--diameter: var(--pf-c-spinner--m-lg--diameter);
    }

    :host([size="xl"]) {
        --pf-c-spinner--diameter: var(--pf-c-spinner--m-xl--diameter);
    }

    /* After the size rules, so it wins over them. */
    :host([inline]) {
        --pf-c-spinner--diameter: var(--pf-c-spinner--m-inline--diameter);
    }

    [part="spinner"] {
        --pf-c-spinner--AnimationDuration: 1.5s;
        --pf-c-spinner--AnimationTimingFunction: cubic-bezier(0.77, 0.005, 0.315, 1);
        --pf-c-spinner--stroke-width-multiplier: 0.1;
        --pf-c-spinner--stroke-width: calc(
            var(--pf-c-spinner--diameter) * var(--pf-c-spinner--stroke-width-multiplier)
        );
        --pf-c-spinner__clipper--Width: var(--pf-c-spinner--diameter);
        --pf-c-spinner__clipper--Height: var(--pf-c-spinner--diameter);
        --pf-c-spinner__clipper--after--BoxShadowColor: var(--pf-c-spinner--Color);
        --pf-c-spinner__clipper--after--Width: var(--pf-c-spinner--diameter);
        --pf-c-spinner__clipper--after--Height: var(--pf-c-spinner--diameter);
        --pf-c-spinner__clipper--after--BoxShadowSpreadRadius: var(--pf-c-spinner--stroke-width);
        --pf-c-spinner__lead-ball--after--BackgroundColor: var(--pf-c-spinner--Color);
        --pf-c-spinner__ball--after--Width: var(--pf-c-spinner--stroke-width);
        --pf-c-spinner__ball--after--Height: var(--pf-c-spinner--stroke-width);
        --pf-c-spinner__tail-ball--after--BackgroundColor: var(--pf-c-spinner--Color);
        position: relative;
        display: inline-block;
        width: var(--pf-c-spinner--diameter);
        height: var(--pf-c-spinner--diameter);
        text-align: left;
        animation: pf-animation-spinner-parent calc(var(--pf-c-spinner--AnimationDuration) * 2)
            var(--pf-c-spinner--AnimationTimingFunction) infinite;
    }

    [part="clipper"] {
        position: absolute;
        width: var(--pf-c-spinner__clipper--Width);
        height: var(--pf-c-spinner__clipper--Height);
        clip-path: inset(0 0 50% 50%);
        animation: pf-animation-spinner__clipper var(--pf-c-spinner--AnimationDuration) linear
            infinite;
    }

    [part="clipper"]::after {
        position: absolute;
        width: var(--pf-c-spinner__clipper--after--Width);
        height: var(--pf-c-spinner__clipper--after--Height);
        clip-path: inset(0 0 0 50%);
        content: "";
        border-radius: 50%;
        box-shadow: inset 0 0 0 var(--pf-c-spinner__clipper--after--BoxShadowSpreadRadius)
            var(--pf-c-spinner__clipper--after--BoxShadowColor);
        animation: pf-animation-spinner__clipper-after var(--pf-c-spinner--AnimationDuration) linear
            infinite;
    }

    [part="leading-ball"] {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        animation: pf-animation-spinner__lead-ball var(--pf-c-spinner--AnimationDuration) linear
            infinite;
    }

    [part="leading-ball"]::after {
        position: absolute;
        top: calc(50% - var(--pf-c-spinner__ball--after--Height) / 2);
        right: 0;
        width: var(--pf-c-spinner__ball--after--Width);
        height: var(--pf-c-spinner__ball--after--Height);
        content: "";
        background-color: var(--pf-c-spinner__lead-ball--after--BackgroundColor);
        border-radius: 50%;
        transform-origin: top right;
    }

    [part="trailing-ball"] {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        animation: pf-animation-spinner__tail-ball var(--pf-c-spinner--AnimationDuration) linear
            infinite;
    }

    [part="trailing-ball"]::after {
        position: absolute;
        top: calc(50% - var(--pf-c-spinner__ball--after--Height) / 2);
        right: 0;
        width: var(--pf-c-spinner__ball--after--Width);
        height: var(--pf-c-spinner__ball--after--Height);
        content: "";
        background-color: var(--pf-c-spinner__tail-ball--after--BackgroundColor);
        border-radius: 50%;
        transform-origin: top right;
    }

    @keyframes pf-animation-spinner-parent {
        0% {
            transform: rotate(0deg);
        }
        50% {
            transform: rotate(540deg);
        }
        100% {
            transform: rotate(1080deg);
        }
    }

    @keyframes pf-animation-spinner__clipper {
        0% {
            transform: rotate(90deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    @keyframes pf-animation-spinner__clipper-after {
        0% {
            transform: rotate(-180deg);
        }
        100% {
            transform: rotate(90deg);
        }
    }

    @keyframes pf-animation-spinner__lead-ball {
        0% {
            transform: rotate(0deg);
        }
        33% {
            transform: rotate(180deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    @keyframes pf-animation-spinner__tail-ball {
        0% {
            transform: rotate(0deg);
        }
        66% {
            transform: rotate(180deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }
`;

export default styles;
