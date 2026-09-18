import { css } from "lit";

export const styles = css`
    :host {
        display: block;
        padding-inline-start: var(--ak-c-pagination--PaddingLeft);
        padding-inline-end: var(--ak-c-pagination--PaddingRight);
    }

    [part="pagination"] {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: flex-end;
        min-width: 8rem;
    }

    [part="pagination-nav"] {
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    [part~="paginator-button"] {
        border: none;
        color: var(--ak-c-pagination--indicator--Color);
    }

    [part~="paginator-button"]:hover {
        border: none;
        color: var(--ak-c-pagination--indicator--Color--hover);
    }

    [part~="paginator-button"]:focus {
        border: none;
        color: var(--ak-c-pagination--indicator--Color--focus);
    }

    [part~="paginator-button"]:active {
        border: none;
        color: var(--ak-c-pagination--indicator--Color--active);
    }

    [part~="paginator-button"]:disabled {
        border: none;
        color: var(--ak-c-pagination--indicator--Color--disabled);
    }

    [part~="paginator-button"] {
        border: none;
        color: var(--ak-c-pagination--indicator--Color);
    }

    [part="total-count"] {
        --pf-c-pagination__total-items--Display: block;
        --pf-c-pagination__total-items--Visibility: visible;

        margin-right: var(--pf-c-pagination--child--MarginRight);
    }

    :host([disabled]) .pf-c-pagination {
        opacity: 0.5;
    }

    :host([theme="dark"]) {
        .pf-c-pagination__nav-control .pf-c-button {
            color: var(--pf-c-button--m-plain--Color);
            --pf-c-button--disabled--Color: var(--pf-c-button--m-plain--disabled--Color);
        }

        .pf-c-pagination__nav-control .pf-c-button:disabled {
            color: var(--pf-c-button--disabled--Color);
        }

        .pf-c-pagination__total-items {
            color: var(--ak-dark-foreground);
        }
    }

    :host {
        display: inline-block;
    }

    @media screen and (min-width: 768px) {
        [part="pagination"] {
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingTop: var(
                --pf-v5-c-pagination--m-bottom__nav-control--c-button--md--PaddingTop
            );
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingRight: var(
                --pf-v5-c-pagination--m-bottom__nav-control--c-button--md--PaddingRight
            );
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingBottom: var(
                --pf-v5-c-pagination--m-bottom__nav-control--c-button--md--PaddingBottom
            );
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingLeft: var(
                --pf-v5-c-pagination--m-bottom__nav-control--c-button--md--PaddingLeft
            );
            --pf-v5-c-pagination--m-bottom--child--MarginRight: var(
                --pf-v5-c-pagination--m-bottom--child--md--MarginRight
            );
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--OutlineOffset: 0;
            --pf-v5-c-pagination--m-bottom--BoxShadow: none;
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--c-menu-toggle--md--Display
            );
            --pf-v5-c-pagination__nav--Display: inline-flex;
            --pf-v5-c-pagination__total-items--Display: none;
        }
    }
    @media screen and (min-width: 1200px) {
        [part="pagination"] {
            --pf-v5-c-pagination--m-bottom--md--PaddingRight: var(
                --pf-v5-c-pagination--m-bottom--xl--PaddingRight
            );
            --pf-v5-c-pagination--m-bottom--md--PaddingLeft: var(
                --pf-v5-c-pagination--m-bottom--xl--PaddingLeft
            );
            --pf-v5-c-pagination__scroll-button--Width: var(
                --pf-v5-c-pagination__scroll-button--xl--Width
            );
            --pf-v5-c-pagination--m-page-insets--inset: var(
                --pf-v5-c-pagination--m-page-insets--xl--inset
            );
        }
    }
    [part="pagination"] > *:not(:last-child):not([part="pagination"]__total-items) {
        margin-inline-end: var(--pf-v5-c-pagination--child--MarginRight);
    }
    [part="pagination"] .pf-v5-c-menu-toggle {
        display: var(--pf-v5-c-pagination--c-menu-toggle--Display);
        font-size: var(--pf-v5-c-pagination--c-menu-toggle--FontSize);
    }
    [part="pagination"].pf-m-bottom {
        --pf-v5-c-pagination--child--MarginRight: var(
            --pf-v5-c-pagination--m-bottom--child--MarginRight
        );
        --pf-v5-c-pagination__nav-control--c-button--PaddingRight: var(
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingRight
        );
        --pf-v5-c-pagination__nav-control--c-button--PaddingLeft: var(
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingRight
        );
        --pf-v5-c-pagination--m-sticky--BoxShadow: var(
            --pf-v5-c-pagination--m-bottom--m-sticky--BoxShadow
        );
        --pf-v5-c-pagination--m-sticky--Top: auto;
        position: sticky;
        inset-block-end: var(--pf-v5-c-pagination--m-bottom--Bottom);
        justify-content: center;
        background-color: var(--pf-v5-c-pagination--m-bottom--BackgroundColor);
        box-shadow: var(--pf-v5-c-pagination--m-bottom--BoxShadow);
    }
    [part="pagination"].pf-m-bottom [part="pagination"]__nav-control .pf-v5-c-button {
        --pf-v5-c-button--PaddingTop: var(
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingTop
        );
        --pf-v5-c-button--PaddingBottom: var(
            --pf-v5-c-pagination--m-bottom__nav-control--c-button--PaddingBottom
        );
        outline-offset: var(--pf-v5-c-pagination--m-bottom__nav-control--c-button--OutlineOffset);
    }
    [part="pagination"].pf-m-bottom.pf-m-static {
        --pf-v5-c-pagination--m-bottom--MarginTop: 0;
        --pf-v5-c-pagination--m-bottom--BorderTopWidth: 0;
        position: relative;
        box-shadow: none;
    }
    [part="pagination"].pf-m-bottom [part="pagination"]__nav-control.pf-m-first,
    [part="pagination"].pf-m-bottom [part="pagination"]__nav-control.pf-m-last,
    [part="pagination"].pf-m-bottom [part="pagination"]__nav-page-select {
        display: none;
    }
    [part="pagination"].pf-m-bottom .pf-v5-c-menu-toggle {
        position: absolute;
        display: var(--pf-v5-c-pagination--m-bottom--c-menu-toggle--Display);
    }
    @media screen and (min-width: 768px) {
        [part="pagination"].pf-m-bottom {
            --pf-v5-c-pagination--m-bottom--BorderTopWidth: 0;
            --pf-v5-c-pagination--m-bottom--MarginTop: 0;
            --pf-v5-c-pagination--m-bottom--Bottom: auto;
            position: relative;
            justify-content: flex-end;
            padding-block-start: var(--pf-v5-c-pagination--m-bottom--md--PaddingTop);
            padding-block-end: var(--pf-v5-c-pagination--m-bottom--md--PaddingBottom);
            padding-inline-start: var(--pf-v5-c-pagination--m-bottom--md--PaddingLeft);
            padding-inline-end: var(--pf-v5-c-pagination--m-bottom--md--PaddingRight);
        }
        [part="pagination"].pf-m-bottom [part="pagination"]__nav-control.pf-m-first,
        [part="pagination"].pf-m-bottom [part="pagination"]__nav-control.pf-m-last,
        [part="pagination"].pf-m-bottom [part="pagination"]__nav-page-select {
            display: block;
        }
        [part="pagination"].pf-m-bottom [part="pagination"]__nav-page-select {
            display: inline-flex;
        }
        [part="pagination"].pf-m-bottom .pf-v5-c-menu-toggle {
            position: relative;
        }
        [part="pagination"].pf-m-bottom [part="pagination"]__nav {
            display: inline-flex;
            flex-basis: auto;
        }
    }
    [part="pagination"].pf-m-sticky {
        --pf-v5-c-pagination--m-bottom--Bottom: 0;
        position: sticky;
        inset-block-start: var(--pf-v5-c-pagination--m-sticky--Top);
        z-index: var(--pf-v5-c-pagination--m-sticky--ZIndex);
        padding-block-start: var(--pf-v5-c-pagination--m-sticky--PaddingTop);
        padding-block-end: var(--pf-v5-c-pagination--m-sticky--PaddingBottom);
        padding-inline-start: var(--pf-v5-c-pagination--m-sticky--PaddingLeft);
        padding-inline-end: var(--pf-v5-c-pagination--m-sticky--PaddingRight);
        background-color: var(--pf-v5-c-pagination--m-sticky--BackgroundColor);
        box-shadow: var(--pf-v5-c-pagination--m-sticky--BoxShadow);
    }
    @media screen and (min-width: 768px) {
        [part="pagination"].pf-m-sticky {
            padding-block-start: var(--pf-v5-c-pagination--m-sticky--md--PaddingTop);
            padding-block-end: var(--pf-v5-c-pagination--m-sticky--md--PaddingBottom);
            padding-inline-start: var(--pf-v5-c-pagination--m-sticky--md--PaddingLeft);
            padding-inline-end: var(--pf-v5-c-pagination--m-sticky--md--PaddingRight);
        }
    }
    [part="pagination"].pf-m-compact {
        --pf-v5-c-pagination--child--MarginRight: var(
            --pf-v5-c-pagination--m-compact--child--MarginRight
        );
    }
    [part="pagination"].pf-m-page-insets {
        --pf-v5-c-pagination--inset: var(--pf-v5-c-pagination--m-page-insets--inset);
    }

    :where(.pf-v5-m-dir-rtl, [dir="rtl"]) [part="pagination"]__nav-control {
        scale: -1 1;
    }

    [part="pagination"]__nav-control .pf-v5-c-button {
        padding-inline-start: var(--pf-v5-c-pagination__nav-control--c-button--PaddingLeft);
        padding-inline-end: var(--pf-v5-c-pagination__nav-control--c-button--PaddingRight);
        font-size: var(--pf-v5-c-pagination__nav-control--c-button--FontSize);
    }
    [part="pagination"].pf-m-compact
        [part="pagination"]__nav-control
        + [part="pagination"]__nav-control {
        margin-inline-start: var(
            --pf-v5-c-pagination--m-compact__nav-control--nav-control--MarginLeft
        );
    }

    [part="pagination"]__nav-page-select {
        display: flex;
        align-items: center;
        padding-inline-start: var(--pf-v5-c-pagination__nav-page-select--PaddingLeft);
        padding-inline-end: var(--pf-v5-c-pagination__nav-page-select--PaddingRight);
    }
    [part="pagination"]__nav-page-select > * {
        font-size: var(--pf-v5-c-pagination__nav-page-select--FontSize);
        white-space: nowrap;
    }
    [part="pagination"]__nav-page-select > *:not(:last-child) {
        margin-inline-end: var(--pf-v5-c-pagination__nav-page-select--child--MarginRight);
    }
    [part="pagination"]__nav-page-select .pf-v5-c-form-control {
        width: var(--pf-v5-c-pagination__nav-page-select--c-form-control--Width);
    }
    [part="pagination"]__total-items {
        display: var(--pf-v5-c-pagination__total-items--Display);
    }

    [part="pagination"].pf-m-display-summary {
        --pf-v5-c-pagination__nav--Display: var(
            --pf-v5-c-pagination--m-display-summary__nav--Display
        );
        --pf-v5-c-pagination--c-menu-toggle--Display: var(
            --pf-v5-c-pagination--m-display-summary--c-menu-toggle--Display
        );
        --pf-v5-c-pagination__total-items--Display: var(
            --pf-v5-c-pagination--m-display-summary__total-items--Display
        );
    }
    [part="pagination"].pf-m-display-full {
        --pf-v5-c-pagination__nav--Display: var(--pf-v5-c-pagination--m-display-full__nav--Display);
        --pf-v5-c-pagination--c-menu-toggle--Display: var(
            --pf-v5-c-pagination--m-display-full--c-menu-toggle--Display
        );
        --pf-v5-c-pagination__total-items--Display: var(
            --pf-v5-c-pagination--m-display-full__total-items--Display
        );
    }
    [part="pagination"].pf-m-inset-none {
        --pf-v5-c-pagination--inset: 0;
    }
    [part="pagination"].pf-m-inset-sm {
        --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--sm);
    }
    [part="pagination"].pf-m-inset-md {
        --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--md);
    }
    [part="pagination"].pf-m-inset-lg {
        --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--lg);
    }
    [part="pagination"].pf-m-inset-xl {
        --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--xl);
    }
    [part="pagination"].pf-m-inset-2xl {
        --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--2xl);
    }
    @media (min-width: 576px) {
        [part="pagination"].pf-m-display-summary-on-sm {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-summary__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-summary--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-summary__total-items--Display
            );
        }
        [part="pagination"].pf-m-display-full-on-sm {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-full__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-full--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-full__total-items--Display
            );
        }
        [part="pagination"].pf-m-inset-none-on-sm {
            --pf-v5-c-pagination--inset: 0;
        }
        [part="pagination"].pf-m-inset-sm-on-sm {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--sm);
        }
        [part="pagination"].pf-m-inset-md-on-sm {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--md);
        }
        [part="pagination"].pf-m-inset-lg-on-sm {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--lg);
        }
        [part="pagination"].pf-m-inset-xl-on-sm {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--xl);
        }
        [part="pagination"].pf-m-inset-2xl-on-sm {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--2xl);
        }
    }
    @media (min-width: 768px) {
        [part="pagination"].pf-m-display-summary-on-md {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-summary__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-summary--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-summary__total-items--Display
            );
        }
        [part="pagination"].pf-m-display-full-on-md {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-full__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-full--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-full__total-items--Display
            );
        }
        [part="pagination"].pf-m-inset-none-on-md {
            --pf-v5-c-pagination--inset: 0;
        }
        [part="pagination"].pf-m-inset-sm-on-md {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--sm);
        }
        [part="pagination"].pf-m-inset-md-on-md {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--md);
        }
        [part="pagination"].pf-m-inset-lg-on-md {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--lg);
        }
        [part="pagination"].pf-m-inset-xl-on-md {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--xl);
        }
        [part="pagination"].pf-m-inset-2xl-on-md {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--2xl);
        }
    }
    @media (min-width: 992px) {
        [part="pagination"].pf-m-display-summary-on-lg {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-summary__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-summary--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-summary__total-items--Display
            );
        }
        [part="pagination"].pf-m-display-full-on-lg {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-full__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-full--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-full__total-items--Display
            );
        }
        [part="pagination"].pf-m-inset-none-on-lg {
            --pf-v5-c-pagination--inset: 0;
        }
        [part="pagination"].pf-m-inset-sm-on-lg {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--sm);
        }
        [part="pagination"].pf-m-inset-md-on-lg {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--md);
        }
        [part="pagination"].pf-m-inset-lg-on-lg {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--lg);
        }
        [part="pagination"].pf-m-inset-xl-on-lg {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--xl);
        }
        [part="pagination"].pf-m-inset-2xl-on-lg {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--2xl);
        }
    }
    @media (min-width: 1200px) {
        [part="pagination"].pf-m-display-summary-on-xl {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-summary__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-summary--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-summary__total-items--Display
            );
        }
        [part="pagination"].pf-m-display-full-on-xl {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-full__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-full--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-full__total-items--Display
            );
        }
        [part="pagination"].pf-m-inset-none-on-xl {
            --pf-v5-c-pagination--inset: 0;
        }
        [part="pagination"].pf-m-inset-sm-on-xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--sm);
        }
        [part="pagination"].pf-m-inset-md-on-xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--md);
        }
        [part="pagination"].pf-m-inset-lg-on-xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--lg);
        }
        [part="pagination"].pf-m-inset-xl-on-xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--xl);
        }
        [part="pagination"].pf-m-inset-2xl-on-xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--2xl);
        }
    }
    @media (min-width: 1450px) {
        [part="pagination"].pf-m-display-summary-on-2xl {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-summary__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-summary--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-summary__total-items--Display
            );
        }
        [part="pagination"].pf-m-display-full-on-2xl {
            --pf-v5-c-pagination__nav--Display: var(
                --pf-v5-c-pagination--m-display-full__nav--Display
            );
            --pf-v5-c-pagination--c-menu-toggle--Display: var(
                --pf-v5-c-pagination--m-display-full--c-menu-toggle--Display
            );
            --pf-v5-c-pagination__total-items--Display: var(
                --pf-v5-c-pagination--m-display-full__total-items--Display
            );
        }
        [part="pagination"].pf-m-inset-none-on-2xl {
            --pf-v5-c-pagination--inset: 0;
        }
        [part="pagination"].pf-m-inset-sm-on-2xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--sm);
        }
        [part="pagination"].pf-m-inset-md-on-2xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--md);
        }
        [part="pagination"].pf-m-inset-lg-on-2xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--lg);
        }
        [part="pagination"].pf-m-inset-xl-on-2xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--xl);
        }
        [part="pagination"].pf-m-inset-2xl-on-2xl {
            --pf-v5-c-pagination--inset: var(--pf-v5-global--spacer--2xl);
        }
    }

    :where(.pf-v5-theme-dark) .pf-v5-c-wizard__header .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-about-modal-box .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-banner .pf-v5-c-button,
    :where(.pf-v5-theme-dark)
        .pf-v5-c-log-viewer.pf-m-dark
        .pf-v5-c-log-viewer__main
        .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-login__header .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-login__footer .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-masthead .pf-v5-c-button,
    :where(.pf-v5-theme-dark)
        .pf-v5-c-page__sidebar-body.pf-m-menu
        .pf-v5-c-context-selector
        .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-page__main-section[class*="pf-m-dark-"] .pf-v5-c-button,
    :where(.pf-v5-theme-dark) .pf-v5-c-page__header .pf-v5-c-button {
        --pf-v5-c-button--m-primary--BackgroundColor: var(--pf-v5-global--primary-color--300);
    }

    :where(.pf-v5-theme-dark) [part="pagination"] {
        --pf-v5-c-pagination--m-sticky--BackgroundColor: var(--pf-v5-global--BackgroundColor--300);
    }
`;

export default styles;
