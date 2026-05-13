import { css } from "lit";

export const styles = css`
    :host {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .ak-v2-c-drawer {
        display: flex;
        flex-direction: column;
        height: 100%;
        overflow-x: hidden;
    }

    :host([position="bottom"]) .ak-v2-c-drawer {
        overflow-x: auto;
        overflow-y: hidden;
    }

    slot {
        display: contents;
    }

    :host([inline]:not([no-border])) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
    :host([inline]:not([resizable])) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
    :host([static]:not([no-border])) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
    :host([static]:not([resizable])) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        padding-inline-start: var(--ak-v2-c-drawer--m-inline__panel--PaddingLeft);
    }

    :host([position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        order: 0;
        margin-inline-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(-100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([position="left"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(-100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
        order: 1;
    }

    :host([position="bottom"]) .ak-v2-c-drawer__main {
        flex-direction: column;
    }

    :host(:not([inline], [static])) .ak-v2-c-drawer__main {
        position: relative;
    }

    :host(:not([inline], [static])) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        position: absolute;
        inset-block-start: 0;
        inset-block-end: 0;
        inset-inline-end: 0;
        max-width: var(--ak-v2-c-drawer__panel--FlexBasis);
        transform: translateX(100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host(:not([inline], [static]))
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([expanded]:not([inline], [static])) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    :host([position="left"]:not([inline], [static]))
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        inset-inline-end: auto;
        inset-inline-start: 0;
        transform: translateX(-100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([position="left"]:not([inline], [static]))
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(-100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([expanded][position="left"]:not([inline], [static]))
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    :host([position="bottom"]:not([inline], [static]))
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        inset-inline-end: 0;
        inset-inline-start: 0;
        inset-block-start: auto;
        inset-block-end: 0;
        max-width: none;
        max-height: var(--ak-v2-c-drawer__panel--FlexBasis);
        transform: translateY(100%);
    }

    :host([position="bottom"][expanded]:not([inline], [static]))
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateY(0);
    }

    :host([class*="pf-m-resizing"]) {
        --ak-v2-c-drawer__panel--TransitionProperty: none;
        pointer-events: none;
    }

    :host([class*="pf-m-resizing"]) .ak-v2-c-drawer__splitter {
        pointer-events: auto;
    }

    .ak-v2-c-drawer__main {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    .ak-v2-c-drawer__content,
    .ak-v2-c-drawer__panel,
    .ak-v2-c-drawer__panel-main {
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
        overflow: auto;
        --ak-v2-c-drawer__content--BackgroundColor: transparent;
    }

    .ak-v2-c-drawer__content {
        z-index: var(--ak-v2-c-drawer__content--ZIndex);
        flex-basis: var(--ak-v2-c-drawer__content--FlexBasis);
        order: 0;
        background-color: var(--ak-v2-c-drawer__content--BackgroundColor);
    }

    .ak-v2-c-drawer__panel {
        position: relative;
        z-index: var(--ak-v2-c-drawer__panel--ZIndex);
        flex-basis: var(--ak-v2-c-drawer__panel--FlexBasis);
        order: 1;
        max-height: var(--ak-v2-c-drawer__panel--MaxHeight);
        gap: var(--ak-v2-global--spacer--sm);
        overflow: auto;
        background-color: var(--ak-v2-c-drawer__panel--BackgroundColor);
        box-shadow: var(--ak-v2-c-drawer__panel--BoxShadow);
        transition-duration: var(--ak-v2-c-drawer__panel--TransitionDuration);
        transition-property: var(--ak-v2-c-drawer__panel--TransitionProperty);
        transition-behavior: allow-discrete;
        -webkit-overflow-scrolling: touch;
    }

    .ak-v2-c-drawer__panel::after {
        position: absolute;
        inset-block-start: 0;
        inset-inline-start: 0;
        width: var(--ak-v2-c-drawer__panel--after--Width);
        height: 100%;
        content: "";
        background-color: var(--ak-v2-c-drawer__panel--after--BackgroundColor);
    }

    @media screen and (min-width: 768px) {
        .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer__panel--FlexBasis: max(
                var(--ak-v2-c-drawer__panel--md--FlexBasis--min),
                min(
                    var(--ak-v2-c-drawer__panel--md--FlexBasis),
                    var(--ak-v2-c-drawer__panel--md--FlexBasis--max)
                )
            );
        }
    }

    @media screen and (min-width: 1200px) {
        :host(:not([width])) .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer__panel--md--FlexBasis: var(--ak-v2-c-drawer__panel--xl--FlexBasis);
        }
    }

    @media screen and (min-width: 1200px) {
        :host([position="bottom"]) .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer__panel--md--FlexBasis: var(
                --ak-v2-c-drawer--m-panel-bottom__panel--xl--FlexBasis
            );
        }
    }

    :where(
            :host(:not([position])),
            :host([position="left"]),
            :host([position="right"]),
            :host([position="start"]),
            :host([position="end"])
        )
        .ak-v2-c-drawer__splitter {
        --ak-v2-c-drawer__splitter--Height: var(--ak-v2-c-drawer__splitter--m-vertical--Height);
        --ak-v2-c-drawer__splitter--Width: var(--ak-v2-c-drawer__splitter--m-vertical--Width);
        --ak-v2-c-drawer__splitter--Cursor: var(--ak-v2-c-drawer__splitter--m-vertical--Cursor);
        --ak-v2-c-drawer__splitter-handle--after--Width: var(
            --ak-v2-c-drawer__splitter--m-vertical__splitter-handle--after--Width
        );
        --ak-v2-c-drawer__splitter-handle--after--Height: var(
            --ak-v2-c-drawer__splitter--m-vertical__splitter-handle--after--Height
        );
        --ak-v2-c-drawer__splitter-handle--after--BorderTopWidth: var(
            --ak-v2-c-drawer__splitter--m-vertical__splitter-handle--after--BorderTopWidth
        );
        --ak-v2-c-drawer__splitter-handle--after--BorderRightWidth: var(
            --ak-v2-c-drawer__splitter--m-vertical__splitter-handle--after--BorderRightWidth
        );
        --ak-v2-c-drawer__splitter-handle--after--BorderBottomWidth: var(
            --ak-v2-c-drawer__splitter--m-vertical__splitter-handle--after--BorderBottomWidth
        );
        --ak-v2-c-drawer__splitter-handle--after--BorderLeftWidth: var(
            --ak-v2-c-drawer__splitter--m-vertical__splitter-handle--after--BorderLeftWidth
        );
    }

    .ak-v2-c-drawer__splitter {
        position: relative;
        display: none;
        width: var(--ak-v2-c-drawer__splitter--Width);
        height: var(--ak-v2-c-drawer__splitter--Height);
        cursor: var(--ak-v2-c-drawer__splitter--Cursor);
        background-color: var(--ak-v2-c-drawer__splitter--BackgroundColor);
    }

    .ak-v2-c-drawer__splitter:hover {
        --ak-v2-c-drawer__splitter-handle--after--BorderColor: var(
            --ak-v2-c-drawer__splitter--hover__splitter-handle--after--BorderColor
        );
    }

    .ak-v2-c-drawer__splitter:focus {
        --ak-v2-c-drawer__splitter-handle--after--BorderColor: var(
            --ak-v2-c-drawer__splitter--focus__splitter-handle--after--BorderColor
        );
    }

    .ak-v2-c-drawer__splitter::after {
        position: absolute;
        inset-block-start: 0;
        inset-block-end: 0;
        inset-inline-start: 0;
        inset-inline-end: 0;
        content: "";
        border: solid var(--ak-v2-c-drawer__splitter--after--BorderColor);
        border-block-start-width: var(--ak-v2-c-drawer__splitter--after--BorderTopWidth);
        border-block-end-width: var(--ak-v2-c-drawer__splitter--after--BorderBottomWidth);
        border-inline-start-width: var(--ak-v2-c-drawer__splitter--after--BorderLeftWidth);
        border-inline-end-width: var(--ak-v2-c-drawer__splitter--after--BorderRightWidth);
    }

    .ak-v2-c-drawer__splitter-handle {
        position: absolute;
        inset-block-start: var(--ak-v2-c-drawer__splitter-handle--Top);
        inset-inline-start: var(--ak-v2-c-drawer__splitter-handle--Left);
        transform: translate(-50%, -50%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"]) .ak-v2-c-drawer__splitter-handle {
        transform: translate(calc(-50% * var(--ak-v2-global--inverse--multiplier)), -50%);
    }

    .ak-v2-c-drawer__splitter-handle::after {
        display: block;
        width: var(--ak-v2-c-drawer__splitter-handle--after--Width);
        height: var(--ak-v2-c-drawer__splitter-handle--after--Height);
        content: "";
        border-color: var(--ak-v2-c-drawer__splitter-handle--after--BorderColor);
        border-style: solid;
        border-block-start-width: var(--ak-v2-c-drawer__splitter-handle--after--BorderTopWidth);
        border-block-end-width: var(--ak-v2-c-drawer__splitter-handle--after--BorderBottomWidth);
        border-inline-start-width: var(--ak-v2-c-drawer__splitter-handle--after--BorderLeftWidth);
        border-inline-end-width: var(--ak-v2-c-drawer__splitter-handle--after--BorderRightWidth);
    }

    @media screen and (min-width: 768px) {
        :host {
            min-width: var(--ak-v2-c-drawer__panel--MinWidth);
        }

        :host([expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            box-shadow: var(--ak-v2-c-drawer--m-expanded__panel--BoxShadow);
        }

        :host([expanded][resizable]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer__panel--md--FlexBasis--min: var(
                --ak-v2-c-drawer__panel--m-resizable--md--FlexBasis--min
            );
            flex-direction: var(--ak-v2-c-drawer__panel--m-resizable--FlexDirection);
            min-width: var(--ak-v2-c-drawer__panel--m-resizable--MinWidth);
        }

        :host([expanded][resizable]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel::after {
            width: 0;
            height: 0;
        }

        :host([expanded][resizable])
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel
            > .ak-v2-c-drawer__splitter {
            flex-shrink: 0;
        }

        :host([expanded][resizable])
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel
            > .ak-v2-c-drawer__panel-main {
            flex-shrink: 1;
        }

        :host([position="left"]) {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: var(
                --ak-v2-c-drawer--m-expanded--m-panel-left__panel--BoxShadow
            );
        }

        :host([position="left"][inline])
            > .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel:not(.pf-m-no-border, .pf-m-resizable),
        :host([position="left"][static])
            > .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel:not(.pf-m-no-border, .pf-m-resizable) {
            padding-inline-start: 0;
            padding-inline-end: var(--ak-v2-c-drawer--m-panel-left--m-inline__panel--PaddingRight);
        }

        :host([position="left"][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            transform: translateX(0);
        }

        :host([position="left"][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel::after {
            inset-inline-start: auto;
            inset-inline-end: 0;
        }

        :host([position="left"][expanded][resizable])
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel
            > .ak-v2-c-drawer__splitter {
            --ak-v2-c-drawer__splitter-handle--Left: var(
                --ak-v2-c-drawer--m-panel-left__splitter-handle--Left
            );
            --ak-v2-c-drawer__splitter--after--BorderRightWidth: 0;
            --ak-v2-c-drawer__splitter--after--BorderLeftWidth: var(
                --ak-v2-c-drawer--m-panel-left__splitter--after--BorderLeftWidth
            );
            order: 1;
        }

        :host([position="bottom"]) {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: var(
                --ak-v2-c-drawer--m-expanded--m-panel-bottom__panel--BoxShadow
            );
            --ak-v2-c-drawer__panel--MaxHeight: 100%;
            --ak-v2-c-drawer__panel--FlexBasis--min: var(
                --ak-v2-c-drawer--m-panel-bottom__panel--FlexBasis--min
            );
            min-width: auto;
            min-height: var(--ak-v2-c-drawer--m-panel-bottom__panel--md--MinHeight);
        }

        :host([position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel::after {
            inset-block-start: 0;
            inset-inline-start: auto;
            width: 100%;
            height: var(--ak-v2-c-drawer--m-panel-bottom__panel--after--Height);
        }

        :host([position="bottom"][resizable]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer__panel--md--FlexBasis--min: var(
                --ak-v2-c-drawer--m-panel-bottom__panel--m-resizable--md--FlexBasis--min
            );
            --ak-v2-c-drawer__panel--m-resizable--FlexDirection: var(
                --ak-v2-c-drawer--m-panel-bottom__panel--m-resizable--FlexDirection
            );
            --ak-v2-c-drawer__panel--m-resizable--MinWidth: 0;
            min-height: var(--ak-v2-c-drawer--m-panel-bottom__panel--m-resizable--MinHeight);
        }

        :host([position="bottom"][resizable])
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel
            > .ak-v2-c-drawer__splitter {
            --ak-v2-c-drawer__splitter-handle--Top: var(
                --ak-v2-c-drawer--m-panel-bottom__splitter-handle--Top
            );
            --ak-v2-c-drawer__splitter--after--BorderRightWidth: 0;
            --ak-v2-c-drawer__splitter--after--BorderBottomWidth: var(
                --ak-v2-c-drawer--m-panel-bottom__splitter--after--BorderBottomWidth
            );
        }

        :host([position="left"][inline]:not([no-border], [resizable]))
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel:not(.pf-m-no-border, .pf-m-resizable),
        :host([position="left"][static]:not([no-border], [resizable]))
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel:not(.pf-m-no-border, .pf-m-resizable) {
            padding-inline-start: 0;
            padding-inline-end: var(--ak-v2-c-drawer--m-panel-left--m-inline__panel--PaddingRight);
        }

        :host([inline][resizable])
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel
            > .ak-v2-c-drawer__splitter {
            --ak-v2-c-drawer__splitter--m-vertical--Width: var(
                --ak-v2-c-drawer--m-inline__splitter--m-vertical--Width
            );
            --ak-v2-c-drawer__splitter-handle--Left: var(
                --ak-v2-c-drawer--m-inline__splitter-handle--Left
            );
            --ak-v2-c-drawer__splitter--after--BorderRightWidth: var(
                --ak-v2-c-drawer--m-inline__splitter--after--BorderRightWidth
            );
            --ak-v2-c-drawer__splitter--after--BorderLeftWidth: var(
                --ak-v2-c-drawer--m-inline__splitter--after--BorderLeftWidth
            );
            outline-offset: var(--ak-v2-c-drawer--m-inline__splitter--focus--OutlineOffset);
        }

        :host([position="bottom"][inline][resizable])
            .ak-v2-c-drawer__main
            > .ak-v2-c-drawer__panel
            > .ak-v2-c-drawer__splitter {
            --ak-v2-c-drawer__splitter--Height: var(
                --ak-v2-c-drawer--m-inline--m-panel-bottom__splitter--Height
            );
            --ak-v2-c-drawer__splitter-handle--Top: var(
                --ak-v2-c-drawer--m-inline--m-panel-bottom__splitter-handle--Top
            );
            --ak-v2-c-drawer__splitter--after--BorderTopWidth: var(
                --ak-v2-c-drawer--m-inline--m-panel-bottom__splitter--after--BorderTopWidth
            );
            --ak-v2-c-drawer__splitter--after--BorderRightWidth: 0;
            --ak-v2-c-drawer__splitter--after--BorderLeftWidth: 0;
        }

        :host([no-panel-border]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: none;
        }

        .ak-v2-c-drawer__splitter {
            display: block;
        }
    }

    @media (min-width: 768px) {
        :host([width="25"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 25%;
        }

        :host([width="33"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 33%;
        }

        :host([width="50"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 50%;
        }

        :host([width="66"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 66%;
        }

        :host([width="75"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 75%;
        }

        :host([width="100"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 100%;
        }
    }

    @media (min-width: 992px) {
        :host([width="25-on-lg"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 25%;
        }

        :host([width="33-on-lg"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 33%;
        }

        :host([width="50-on-lg"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 50%;
        }

        :host([width="66-on-lg"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 66%;
        }

        :host([width="75-on-lg"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 75%;
        }

        :host([width="100-on-lg"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 100%;
        }
    }

    @media (min-width: 1200px) {
        :host([width="25-on-xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 25%;
        }

        :host([width="33-on-xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 33%;
        }

        :host([width="50-on-xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 50%;
        }

        :host([width="66-on-xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 66%;
        }

        :host([width="75-on-xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 75%;
        }

        :host([width="100-on-xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 100%;
        }
    }

    @media (min-width: 1450px) {
        :host([width="25-on-2xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 25%;
        }

        :host([width="33-on-2xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 33%;
        }

        :host([width="50-on-2xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 50%;
        }

        :host([width="66-on-2xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 66%;
        }

        :host([width="75-on-2xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 75%;
        }

        :host([width="100-on-2xl"]) {
            --ak-v2-c-drawer__panel--md--FlexBasis: 100%;
        }
    }

    @media (min-width: 768px) {
        :host([inline]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content,
        :host([static]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
            flex-shrink: 1;
        }

        :host([inline]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
        :host([static]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: none;
        }

        :host([inline]:not([no-border])),
        :host([static]:not([no-border])) {
            background-color: var(
                --ak-v2-c-drawer--m-inline--m-expanded__panel--after--BackgroundColor
            );
        }
    }

    :host([inline]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
        overflow-x: auto;
    }

    :host([inline]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        transform: translateX(0);
    }

    :host([inline][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        margin-inline-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(-100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline][position="left"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(-100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline][position="left"][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([inline][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-block-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateY(100%);
    }

    :host([inline][expanded][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-block-end: 0;
        transform: translateY(0);
    }

    :host([static]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    :host([static][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([static][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    @media (min-width: 992px) {
        :host([inline-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content,
        :host([static-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
            flex-shrink: 1;
        }

        :host([inline-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
        :host([static-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: none;
        }

        :host([inline-on-lg]:not([no-border])),
        :host([static-on-lg]:not([no-border])) {
            background-color: var(
                --ak-v2-c-drawer--m-inline--m-expanded__panel--after--BackgroundColor
            );
        }
    }

    :host([inline-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
        overflow-x: auto;
    }

    :host([inline-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline-on-lg])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline-on-lg][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        transform: translateX(0);
    }

    :host([inline-on-lg][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        margin-inline-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(-100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline-on-lg][position="left"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(-100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline-on-lg][position="left"][expanded])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([inline-on-lg][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-block-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateY(100%);
    }

    :host([inline-on-lg][expanded][position="bottom"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        margin-block-end: 0;
        transform: translateY(0);
    }

    :host([static-on-lg]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    :host([static-on-lg][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([static-on-lg][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    @media (min-width: 1200px) {
        :host([inline-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content,
        :host([static-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
            flex-shrink: 1;
        }

        :host([inline-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
        :host([static-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: none;
        }

        :host([inline-on-xl]:not([no-border])),
        :host([static-on-xl]:not([no-border])) {
            background-color: var(
                --ak-v2-c-drawer--m-inline--m-expanded__panel--after--BackgroundColor
            );
        }
    }

    :host([inline-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
        overflow-x: auto;
    }

    :host([inline-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline-on-xl])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline-on-xl][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        transform: translateX(0);
    }

    :host([inline-on-xl][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        margin-inline-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(-100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline-on-xl][position="left"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(-100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline-on-xl][position="left"][expanded])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([inline-on-xl][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-block-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateY(100%);
    }

    :host([inline-on-xl][expanded][position="bottom"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        margin-block-end: 0;
        transform: translateY(0);
    }

    :host([static-on-xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    :host([static-on-xl][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([static-on-xl][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    @media (min-width: 1450px) {
        :host([inline-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content,
        :host([static-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
            flex-shrink: 1;
        }

        :host([inline-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel,
        :host([static-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
            --ak-v2-c-drawer--m-expanded__panel--BoxShadow: none;
        }

        :host([inline-on-2xl]:not([no-border])),
        :host([static-on-2xl]:not([no-border])) {
            background-color: var(
                --ak-v2-c-drawer--m-inline--m-expanded__panel--after--BackgroundColor
            );
        }
    }

    :host([inline-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__content {
        overflow-x: auto;
    }

    :host([inline-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline-on-2xl])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline-on-2xl][expanded]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        transform: translateX(0);
    }

    :host([inline-on-2xl][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-start: 0;
        margin-inline-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateX(-100%);
    }

    :where(.ak-v2-m-dir-rtl, [dir="rtl"])
        :host([inline-on-2xl][position="left"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        transform: translateX(calc(-100% * var(--ak-v2-global--inverse--multiplier)));
    }

    :host([inline-on-2xl][position="left"][expanded])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([inline-on-2xl][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-block-end: calc(var(--ak-v2-c-drawer__panel--FlexBasis) * -1);
        transform: translateY(100%);
    }

    :host([inline-on-2xl][expanded][position="bottom"])
        .ak-v2-c-drawer__main
        > .ak-v2-c-drawer__panel {
        margin-block-end: 0;
        transform: translateY(0);
    }

    :host([static-on-2xl]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    :host([static-on-2xl][position="left"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        margin-inline-end: 0;
        transform: translateX(0);
    }

    :host([static-on-2xl][position="bottom"]) .ak-v2-c-drawer__main > .ak-v2-c-drawer__panel {
        transform: translateX(0);
    }

    @media screen and (min-width: 1200px) {
        :host([position="bottom"]) {
            --ak-v2-c-drawer__panel--MinWidth: auto;
            --ak-v2-c-drawer__panel--MinHeight: var(
                --ak-v2-c-drawer--m-panel-bottom__panel--xl--MinHeight
            );
        }
    }
`;
//
export default styles;
