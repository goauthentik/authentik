import { css } from "lit";

export const styles = css`
    slot {
        display: contents;
    }

    :host {
        display: block;
        min-block-size: 100dvh;
        width: 100%;
    }

    [part="flow"] {
        display: grid;
        min-block-size: 100dvh;
        width: 100%;
        color: var(--ak-v2-c-flow--Color);
        background: var(--ak-v2-c-flow__card--BackgroundColor);
    }

    /* -------- The card with branding & the executor ------------------------ */

    [part="main"] {
        position: relative;
        background: var(--ak-v2-c-flow__card--BackgroundColor);
        border-radius: var(--ak-v2-c-flow__card--BorderRadius);
        display: flex;
        flex-direction: column;
        gap: var(--ak-v2-c-flow__card--Gap);
        inline-size: var(--ak-v2-c-flow__card--InlineSize);
        min-block-size: var(--ak-v2-c-flow__card--MinBlockSize);
        padding: var(--ak-v2-c-flow__card--Padding);
    }

    [part="branding"] {
        display: flex;
        justify-content: center;
        padding-block-start: var(--ak-v2-c-flow__branding--PaddingBlockStart);
        padding-inline: var(--ak-v2-c-flow__branding--PaddingInline);
        padding-block-end: var(--ak-v2-c-flow__branding--PaddingBlockEnd);
    }

    [part="branding"] > img,
    [part="branding"] > svg {
        display: block;
        max-width: var(--ak-v2-c-flow__branding__content--MaxWidth);
    }

    [part="executor"] {
        display: flex;
        justify-content: center;
    }

    /* -------- The footer with brand links and salesmark -------------------- */

    [part="footer"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-self: end;
        color: var(--ak-v2-c-flow__footer--Color);
    }

    [part="footer"] > slot[name="footer"] {
        display: contents;
    }

    .ak-v2-c-salesmark {
        align-items: center;
        display: flex;
        flex-direction: row;
        gap: 0.25rem;
        justify-content: center;
        padding-block-end: var(--ak-v2-c-brand-links--Gap);
        text-align: center;
        white-space: nowrap;
    }

    .ak-v2-c-salesmark svg {
        height: 2rex;
    }

    [part="loading-overlay"] {
        position: absolute;
        inset: 0;
        border-radius: inherit;
    }

    [part="content"] {
        display: block;
        block-size: 100%;
        inline-size: 100%;
        overflow: hidden;
    }

    [part="content-iframe"] {
        inline-size: 100%;
        block-size: 100%;
        border: 0;
    }

    /* -------- Layouts ----------------------------------------------------- */

    /* The (CSS) default layout is left-sidebar */

    [part="flow"] {
        grid-template-columns: 1fr;
        grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
    }

    [part="main"] {
        grid-row: 2 / 3;
        grid-column: 1 / 2;
    }

    [part="footer"] {
        grid-row: 3/4;
        grid-column: 1 / 2;
    }

    /* -------- Layouts when the browser width is greater than 560px -------------------- */

    @media (width > 560px) {
        [part="flow"] {
            grid-template-columns: 1fr var(--ak-v2-c-flow__card--InlineSize) 1fr;
            background-color: transparent;
        }

        [part="main"] {
            border-radius: var(--ak-v2-c-flow__card--BorderRadius);
        }

        [part="main"] {
            grid-row: 2 / 3;
            grid-column: 2 / 3;
        }

        [part="footer"] {
            grid-row: 3 / 4;
            grid-column: 1 / 4;
        }

        [part="footer"] {
            color: var(--ak-v2-c-flow--InvertedColor);
            background-color: var(--ak-v2-c-flow__footer--Background);
        }
    }

    /* -------- Sidebar left -------------------- */

    @media (width > 560px) {
        :host([data-layout^="sidebar_left"]) [part="flow"] {
            --card: var(--ak-v2-c-flow__card--InlineSize);
            grid-template-columns: var(--card) 1fr;
            grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
        }

        :host([data-layout^="sidebar_left"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 1 / 2;
        }

        :host([data-layout^="sidebar_left"]) [part="iframe"] {
            grid-row: 1 / 4;
            grid-column: 2 / 3;
        }

        :host([data-layout^="sidebar_left"]) [part="flow"]::before {
            content: "";
            background: var(--ak-v2-c-flow__card--BackgroundColor);
            grid-row: 1 / 4;
            grid-column: 1 / 2;
        }

        :host([data-layout^="sidebar_left_frame_background"]) [part="iframe"] {
            grid-row: 1 / 4;
            grid-column: 2 / 3;
        }

        :host([data-layout^="sidebar_left"]) [part="footer"] {
            grid-row: 3/4;
            grid-column: 1 / 2;
        }
    }

    /* -------- Sidebar right -------------------- */

    @media (width > 560px) {
        :host([data-layout^="sidebar_right"]) [part="flow"] {
            --card: var(--ak-v2-c-flow__card--InlineSize);
            grid-template-columns: 1fr var(--card);
            grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
        }

        :host([data-layout^="sidebar_right"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 2 / 3;
        }

        :host([data-layout^="sidebar_right"]) [part="flow"]::before {
            content: "";
            background: var(--ak-v2-c-flow__card--BackgroundColor);
            grid-row: 1 / 4;
            grid-column: 2 / 3;
        }

        :host([data-layout^="sidebar_right_frame_background"]) [part="iframe"] {
            grid-row: 1 / 4;
            grid-column: 1 / 2;
        }

        :host([data-layout^="sidebar_right"]) [part="footer"] {
            grid-row: 3/4;
            grid-column: 2 / 3;
        }
    }

    /* -------- Styles when the browser width is greater than 992px -------------------- */

    /* -------- Content left -------------------- */

    @media (width > 992px) {
        :host([data-layout="content_left"]) [part="flow"] {
            --card: var(--ak-v2-c-flow__card--InlineSize);
            --meta: calc(var(--ak-v2-c-flow__card--InlineSize) * 0.66666);

            grid-template-columns: 1fr var(--card) var(--meta) 1fr;
            grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
        }

        :host([data-layout="content_left"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 2 / 3;
        }

        :host([data-layout="content_left"]) [part="footer"] {
            align-self: stretch;
            grid-row: 2 / 3;
            grid-column: 3 / 4;
        }
    }

    /* -------- Content right -------------------- */

    @media (width > 992px) {
        :host([data-layout="content_right"]) [part="flow"] {
            --card: var(--ak-v2-c-flow__card--InlineSize);
            --meta: calc(var(--ak-v2-c-flow__card--InlineSize) * 0.66666);
            grid-template-columns: 1fr var(--meta) var(--card) 1fr;

            grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
        }

        :host([data-layout="content_right"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 3 / 4;
        }

        :host([data-layout="content_right"]) [part="footer"] {
            align-self: stretch;
            grid-row: 2 / 3;
            grid-column: 2 / 3;
        }
    }
`;

export default styles;
