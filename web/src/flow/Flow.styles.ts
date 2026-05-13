import { css } from "lit";

export const styles = css`
    :host {
        display: grid;
        min-block-size: 100dvh;
        color: var(--ak-v2-c-flow--Color);
        isolation: isolate;
    }

    [part="panel"] {
        display: grid;
        min-block-size: 0;
    }

    [part="head-spacer"] {
        block-size: var(--ak-v2-c-flow--Gutter);
    }

    [part="main"] {
        position: relative;
        background: var(--ak-v2-c-flow__card--BackgroundColor);
        border-radius: var(--ak-v2-c-flow__card--BorderRadius);
        box-shadow: var(--ak-v2-c-flow__card--BoxShadow);
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
        padding-block-start: var(--ak-v2-c-flow__header--PaddingBlockStart);
        padding-inline: var(--ak-v2-c-flow__header--PaddingInline);
        padding-block-end: var(--ak-v2-c-flow__header--PaddingBlockEnd);
    }

    [part="footer"] {
        display: flex;
        flex-direction: column;
        gap: var(--ak-v2-c-flow__footer--Gap);
        padding: var(--ak-v2-c-flow--Gutter);
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

    :host([data-layout="stacked"]),
    :host(:not([data-layout])) {
        grid-template-columns: 1fr;
        grid-template-rows: 1fr auto;
    }

    :where(:host([data-layout="stacked"]), :host(:not([data-layout]))) [part="panel"] {
        grid-row: 1 / -1;
        grid-template-rows: var(--ak-flow-vertical-offset) auto 1fr auto;
        grid-template-columns: 1fr;
        justify-items: center;
    }

    :where(:host([data-layout="stacked"]), :host(:not([data-layout]))) .pf-c-login__header {
        grid-row: 1;
    }

    :where(:host([data-layout="stacked"]), :host(:not([data-layout]))) .pf-c-login__main {
        grid-row: 2;
    }

    :where(:host([data-layout="stacked"]), :host(:not([data-layout]))) .pf-c-login__footer {
        grid-row: 4;
        inline-size: 100%;
        background: var(--ak-flow-band-bg);
        align-items: center;
    }
`;

export default styles;
