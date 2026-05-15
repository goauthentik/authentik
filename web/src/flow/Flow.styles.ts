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

    /*
     * The salesmark does not get a '[part]' reference; it should be *hard*
     * for someone to modify or delete it.
     */
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
        /* Yes, "rex"; we're controlling the height of the Authentik logo, and 
         * it has to fit in a text stream. 
         */
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

    [part="header"] {
        position: relative;
        grid-row: 1 / 2;
        grid-column: 1 / -1;
    }

    [part="main"] {
        grid-row: 2 / 3;
        grid-column: 1 / 2;
    }

    [part="footer"] {
        grid-row: 3 / 4;
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

        /* Memory-preserving notice: in sidebar mode, we restrict the header to
         * the same width as the sidebar;the locale and inspect buttons are now
         * constrained to fit in the sidebar, which is the correct design. This
         * applies to sidebar_right as well. 
         */
        :host([data-layout^="sidebar_left"]) [part="header"] {
            grid-column: 1 / 2;
        }

        :host([data-layout^="sidebar_left"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 1 / 2;
        }

        /* Ensures the entire sidebar has the solid background, not just the 
         * components 
         */
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
            grid-row: 3 / 4;
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

        :host([data-layout^="sidebar_right"]) [part="header"] {
            grid-column: 2 / 3;
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
            grid-row: 3 / 4;
            grid-column: 2 / 3;
        }
    }

    /* -------- Styles when the browser width is greater than 992px -------------------- */

    /* -------- Content left, AKA Patternfly Classic -------------------- */

    @media (width > 992px) {
        :host([data-layout="content_left"]) [part="flow"] {
            --card: var(--ak-v2-c-flow__card--InlineSize);
            --meta: var(--ak-v2-c-flow__meta--InlineSize);

            grid-template-columns: 1fr var(--card) var(--meta) 1fr;
            grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
        }

        /* With 'main' and 'footer' placed immediately adjacent, tune the 
         * borders to create a seamless impression.
         */
        :host([data-layout="content_left"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 2 / 3;
            border-radius: unset;
            border-top-left-radius: var(--ak-v2-c-flow__card--BorderRadius);
            border-bottom-left-radius: var(--ak-v2-c-flow__card--BorderRadius);
        }

        :host([data-layout="content_left"]) [part="footer"] {
            grid-row: 2 / 3;
            grid-column: 3 / 4;
            border-radius: unset;
            border-top-right-radius: var(--ak-v2-c-flow__card--BorderRadius);
            border-bottom-right-radius: var(--ak-v2-c-flow__card--BorderRadius);
            align-self: stretch;
        }
    }

    /* -------- Content right -------------------- */

    @media (width > 992px) {
        :host([data-layout="content_right"]) [part="flow"] {
            --card: var(--ak-v2-c-flow__card--InlineSize);
            --meta: var(--ak-v2-c-flow__meta--InlineSize);

            grid-template-columns: 1fr var(--meta) var(--card) 1fr;
            grid-template-rows: var(--ak-v2-c-flow--VerticalOffset) auto 1fr;
        }

        :host([data-layout="content_right"]) [part="main"] {
            grid-row: 2 / 3;
            grid-column: 3 / 4;
            border-radius: unset;
            border-top-right-radius: var(--ak-v2-c-flow__card--BorderRadius);
            border-bottom-right-radius: var(--ak-v2-c-flow__card--BorderRadius);
        }

        :host([data-layout="content_right"]) [part="footer"] {
            align-self: stretch;
            grid-row: 2 / 3;
            grid-column: 2 / 3;
            border-radius: unset;
            border-top-left-radius: var(--ak-v2-c-flow__card--BorderRadius);
            border-bottom-left-radius: var(--ak-v2-c-flow__card--BorderRadius);
        }
    }

    /* -------- Accessory: Locale Selection ---------------------------------- */

    [part="locale-select"],
    [part="locale-select"].style-scope {
        /* Compatibility mode */
        color: var(--ak-v2-c-flow__locale--Color);
        position: absolute;
        inset-block-start: var(--ak-v2-c-flow__locale--Padding);
        inset-inline-start: var(--ak-v2-c-flow__locale--Padding);
        font-weight: 500;
        z-index: 100;

        /* Slight differences in browser hover states. */
        &:has(select:hover),
        &:hover {
            --ak-c-locale-select--label--Color: var(
                --ak-v2-c-flow__locale--Color--hover,
                var(--ak-v2-c-flow__locale--Color)
            );
            --ak-c-locale-select--BackgroundColor: var(
                --ak-v2-c-flow__locale--BackgroundColor--hover
            );
            --ak-c-locale-select--TextDecorationColor: var(--ak-c-locale-select--label--Color);
            --ak-c-locale-select__after--Opacity: 1;

            --ak-c-locale-select--Color: var(--ak-v2-c-flow__locale--Color--hover);

            @media (prefers-contrast: more) {
                --ak-c-locale--select--OutlineColor: var(--pf-global--primary-color--dark-100);
            }
        }

        filter: var(--ak-global--BackgroundContrastFilter);

        /* At least a third of the card cut-off is available. */
        @media (width <= 61.25rem) and (height <= 61.25rem) {
            --ak-global--BackgroundContrastFilter: none;
            --ak-v2-c-flow__locale--Color: var(--ak-c-login__main--Color);

            grid-area: main;
        }

        @media (width <= 61.25rem) and (height <= 61.25rem) and (not (prefers-contrast: more)) {
            --ak-c-locale-select--Opacity: 0;

            &:hover {
                --ak-c-locale-select--Opacity: 1;
                --ak-c-locale-select__after--Opacity: 1;
            }
        }

        /* Card is fully masked to mobile background. */
        @media (width <= 35rem) {
            grid-row: header;
        }
    }

    /* -------- Accessory: Flow Inspector Button ---------------------------------- */

    ak-flow-inspector-button {
        position: absolute;
        inset-block-start: var(--ak-v2-c-flow__locale--Padding);
        inset-inline-end: var(--ak-v2-c-flow__locale--Padding);

        z-index: 100;
    }
`;

export default styles;
