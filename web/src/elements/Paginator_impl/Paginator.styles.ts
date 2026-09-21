import { css } from "lit";

export const styles = css`
    :host {
        display: block;
        padding-inline-start: var(--ak-c-pagination--PaddingLeft);
        padding-inline-end: var(--ak-c-pagination--PaddingRight);
        --pf-c-pagination__total-items--Display: none;
        --pf-c-pagination__total-items--Visibility: hidden;
    }

    :host([compact]) {
        --ak-c-pagination--Gap: var(--ak-c-pagination--m-compact--Gap);
        --ak-c-pagination--nav-buttons--Gap: var(--ak-c-pagination--m-compact--nav-buttons--Gap);
    }

    [part="pagination"] {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: var(--ak-c-pagination--JustifyContent);
        min-width: var(--ak-c-pagination--MinWidth);
        gap: var(--ak-c-pagination--Gap);
        font-size: var(--ak-c-pagination--FontSize);
    }

    [part="pagination-nav"] {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: var(--ak-c-pagination--nav-buttons--Gap);
    }

    [part~="paginator-button"] {
        border: none;
        color: var(--ak-c-pagination--indicator--Color);
        background-color: inherit;
        padding-inline-start: 0;
        padding-inline-end: 0;
    }

    [part~="paginator-button"] {
        border: none;
        color: var(--ak-c-pagination--indicator--Color);
    }

    [part~="paginator-button"]:hover {
        border: none;
        --ak-c-pagination--indicator--Color: var(--ak-c-pagination--indicator--hover--Color);
    }

    [part~="paginator-button"]:focus {
        border: none;
        --ak-c-pagination--indicator--Color: var(--ak-c-pagination--indicator--focus--Color);
    }

    [part~="paginator-button"]:active {
        border: none;
        --ak-c-pagination--indicator--Color: var(--ak-c-pagination--indicator--active--Color);
    }

    [part~="paginator-button"]:disabled {
        border: none;
        --ak-c-pagination--indicator--Color: var(--ak-c-pagination--indicator--disabled--Color);
    }

    [part="page-select"],
    [part="page-select"] > * {
        white-space: nowrap;
    }

    [part="total-count"] {
        display: var(--pf-c-pagination__total-items--Display);
        visibility: var(--pf-c-pagination__total-items--Visibility);
        color: var(--ak-c-pagination--total-count--Color);
    }

    [part="total-count"] b {
        font-weight: 500;
    }

    [part="page-select-control"] {
        width: calc(var(--ak-c-pagination__page-select--form-control--width) + 2em);
    }

    :host([disabled]) .pf-c-pagination {
        opacity: 0.5;
    }

    :host {
        display: inline-block;
    }

    /* Yes, EM. It's about the size-as-displayed */
    @media (min-width: 40em) {
        [part="total-count"] {
            --pf-c-pagination__total-items--Display: inline-block;
            --pf-c-pagination__total-items--Visibility: visible;
        }
        [part="pagination"] {
            --ak-c-pagination--MinWidth: var(--ak-c-pagination--full--MinWidth);
        }
    }
`;

export default styles;
