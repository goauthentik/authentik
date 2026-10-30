import { css } from "lit";

export const styles = css`
    :host {
        display: block;
        font-family: var(--pf-global--FontFamily--monospace, "monospace");
    }

    .collapsable::before {
        display: inline-flex;
        font-size: var(--pf-global--FontSize--sm);
        content: "▶";
        width: 1.2em;
        height: 1.2em;
        align-items: center;
        justify-content: center;
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
        top: 0.2rem;
        bottom: 0.2rem;
        left: -0.6;
    }

    ul ul:hover::before {
        border-left: 2px solid #bee1f4;
    }
`;

export default styles;
