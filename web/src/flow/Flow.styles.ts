import { css } from "lit";

export const styles = css`
    :host {
        display: grid;
        min-block-size: 100dvh;
        min-inline-size: 100vw;
        color: var(--ak-v2-c-flow--Color);
    }

    [part="panel"] {
        display: grid;
        min-block-size: 0;
        max-width: 35rem;
        background: var(--ak-v2-c-flow__card--BackgroundColor);
    }

    [part="headroom"] {
        block-size: var(--ak-v2-c-flow--Gutter);
        grid-row: 1/2;
    }

    /* -------- The card with branding & the executor ------------------------ */

    [part="main"] {
        grid-row: 2/3;
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
        grid-row: 3/4;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-self: end;
        color: var(--ak-v2-c-flow__footer--Color);
    }

    [part="footer"] > slot[name="footer"] {
        display: contents;
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
`;

export default styles;
