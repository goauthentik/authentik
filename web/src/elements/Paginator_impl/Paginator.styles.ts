import { css } from "lit";

export const styles = css`
    :host {
        display: block;
    }

    .pf-c-pagination {
        min-width: 8rem;
    }

    .pf-c-pagination__total-items {
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
`;

export default styles;
