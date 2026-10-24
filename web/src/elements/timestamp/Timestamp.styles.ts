import { css } from "lit";

export const styles = css`
    :host {
        font-size: var(--ak-timestamp--FontSize);
        font-style: var(--ak-timestamp--FontStyle);
        color: var(--ak-timestamp--Color);
        background-color: var(--ak-timestamp--BackgroundColor);
        word-break: var(--ak-timestamp--WordBreak);
    }

    [part="label"] {
        display: inline-block;
    }

    [part="elapsed"] {
        display: inline-block;
    }

    [part="datetime"] {
        display: inline-block;
    }
`;

export default styles;
