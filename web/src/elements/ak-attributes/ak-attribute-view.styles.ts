import { css } from "lit";

export const styles = css`
    .row {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        padding: 0.2rem 0 0.2rem 0.75rem;
        position: relative;
    }

    .nested {
        margin-left: 0.4rem;
        border-left: 1px solid var(--ak-border-strong, #ccc);
        padding-left: 0;
    }

    .key {
        font-weight: 600;
        color: var(--ak-text-secondary, #666);
    }

    .val-string {
        color: var(--ak-accent-green, #2e6e4e);
    }

    .val-number {
        color: var(--ak-accent-amber, #8a5a2a);
    }

    .val-bool,
    .val-null {
        color: var(--ak-accent-violet, #7a5ac4);
    }

    .hint {
        color: var(--ak-text-muted, #999);
        font-size: 0.85em;
    }
`;
//
export default styles;
