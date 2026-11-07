import { css } from "lit";

export const styles = css`
    [part="toolbar"] {
        display: flex;
        flex-direction: row;
        gap: var(--ak-c-attribute-view__toolbar--Gap);
    }

    [part="copy-button"] {
        display: grid;
        place-items: center;
    }

    [part="copy-button"] svg {
        height: 1em;
        width: fit-content;
    }

    pre {
        font-family: var(--ak-c-attribute-view--FontFamily);
        text-wrap: wrap;
    }
`;

//
export default styles;
