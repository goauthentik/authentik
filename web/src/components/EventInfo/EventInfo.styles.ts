import { css } from "lit";

export const styles = css`
    code {
        display: block;
        white-space: pre-wrap;
        word-break: break-all;
    }
    .pf-l-flex {
        justify-content: space-between;
    }
    .pf-l-flex__item {
        min-width: 25%;
    }
    iframe {
        width: 100%;
        height: 50rem;
    }
`;

export default styles;
