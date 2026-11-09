import { css } from "lit";

export const styles = css`
    :host {
        display: block;
        font-family: var(--ak-c-structured-view--FontFamily);
    }

    pre {
        font-family: var(--ak-c-structured-view--FontFamily);
        margin-left: var(--pf-global--spacer--xl);
        margin-top: 0;
    }

    [part="oneline-string"],
    [part="multiline-string"] {
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    summary {
        cursor: pointer;
        list-style: none;
    }

    summary::-webkit-details-marker {
        display: none;
    }

    summary::before {
        display: grid;
        font-size: var(--pf-global--FontSize--sm);
        content: "▶";
        width: 1.2em;
        height: 100%;
        place-items: center;
        transition: var(--pf-global--Transition);
    }

    details[open] > summary::before {
        transform: rotate(90deg);
    }

    @media (prefers-reduced-motion: reduce) {
        summary::before {
            transition: none;
        }
    }

    [part="tree-key"] {
        display: inline-flex;
        align-items: flex-start;
        color: var(--ak-c-structured-view__key--Color);
    }

    [part="tree-item"] {
        white-space: nowrap;
    }

    [part="keycount"] {
        font-size: var(--ak-c-structured-view__keycount--FontSize);
        color: var(--ak-c-structured-view__keycount--Color);
    }

    ul {
        color: var(--ak-c-structured-view__list--Color);
        padding: 0;
        clear: both;
    }

    ul,
    li {
        list-style: none;
        position: relative;
    }

    li ul > li {
        position: relative;
        margin-left: var(--ak-c-structured-view__toggle--Width);
        padding-left: 0;
    }

    ul ul::before {
        content: "";
        border-left: var(--ak-c-structured-view__nested-indicator--Width)
            var(--ak-c-structured-view__nested-indicator--Style)
            var(--ak-c-structured-view__nested-indicator--Color);
        position: absolute;
        width: var(--ak-c-structured-view__toggle--Width);
        top: 0.2rem;
        bottom: 0.2rem;
        transform: translateX(calc(var(--ak-c-structured-view__toggle--Width) / 3.33));
    }

    ul ul:hover::before {
        --ak-c-structured-view__nested-indicator--Width: var(
            --ak-c-structured-view__nested-indicator--Width--hover
        );
    }
`;

export default styles;
