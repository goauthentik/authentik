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
        color: var(--ak-c-tree-view__key--Color);
    }

    [part="tree-item"] {
        white-space: nowrap;
    }

    ul {
        color: var(--ak-c-tree-view__list--Color);
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
        margin-left: var(--ak-c-tree-view__toggle--Width);
        padding-left: 0;
    }

    ul ul::before {
        content: "";
        border-left: var(--ak-c-tree-view__nested-indicator--Width)
            var(--ak-c-tree-view__nested-indicator--Style)
            var(--ak-c-tree-view__nested-indicator--Color);
        position: absolute;
        width: var(--ak-c-tree-view__toggle--Width);
        top: 0.2rem;
        bottom: 0.2rem;
        transform: translateX(calc(var(--ak-c-tree-view__toggle--Width) / 3.33));
    }

    ul ul:hover::before {
        --ak-c-tree-view__nested-indicator--Width: var(
            --ak-c-tree-view__nested-indicator--Width--hover
        );
    }
`;

export default styles;
