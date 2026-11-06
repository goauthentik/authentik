import { css } from "lit";

export const styles = css`
    :host {
        display: block;
        font-family: var(--pf-global--FontFamily--monospace, "monospace");
    }

    pre {
        font-family: var(--pf-global--FontFamily--monospace, "monospace");
        margin-left: var(--pf-global--spacer--xl);
        margin-top: 0;
    }

    .collapsable::before {
        display: grid;
        font-size: var(--pf-global--FontSize--sm);
        content: "▶";
        width: 1.2em;
        height: 100%;
        place-items: center;
        transition: var(--pf-global--Transition);
        transform: rotate(90deg);
    }

    .collapsable.collapsed::before {
        transform: rotate(0);
    }

    [part="tree-key"] {
        display: inline-flex;
        align-items: flex-start;
        color: var(--pf-global--Color--100);
    }

    [part="tree-item"] {
        white-space: nowrap;
    }

    ul {
        color: var(--pf-global--Color--100);
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
        margin-left: 1.2rem;
        padding-left: 0;
    }

    ul ul::before {
        content: "";
        border-left: 1px solid #bee1f4;
        position: absolute;
        width: 1.2em;
        top: 0.2rem;
        bottom: 0.2rem;
        transform: translateX(33.333%);
    }

    ul ul:hover::before {
        border-left: 2px solid #bee1f4;
    }
`;

export default styles;
