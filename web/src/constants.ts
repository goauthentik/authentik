import { css } from "lit-element";

export const PRIMARY_CLASS = "pf-m-primary";
export const SUCCESS_CLASS = "pf-m-success";
export const ERROR_CLASS = "pf-m-danger";
export const PROGRESS_CLASS = "pf-m-in-progress";
export const CURRENT_CLASS = "pf-m-current";
export const ColorStyles = css`
    .pf-m-success {
        color: var(--pf-global--success-color--100);
    }
    .pf-c-button.pf-m-success {
        color: var(--pf-c-button--m-primary--Color);
        background-color: var(--pf-global--success-color--100);
    }
    .pf-m-warning {
        color: var(--pf-global--warning-color--100);
    }
    .pf-c-button.pf-m-warning {
        color: var(--pf-c-button--m-primary--Color);
        background-color: var(--pf-global--warning-color--100);
    }
    .pf-m-danger {
        color: var(--pf-global--danger-color--100);
    }
    .pf-c-button.pf-m-danger {
        color: var(--pf-c-button--m-primary--Color);
        background-color: var(--pf-global--danger-color--100);
    }
`;
export const VERSION = "2021.2.1-stable";
