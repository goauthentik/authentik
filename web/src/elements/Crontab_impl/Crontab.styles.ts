/**
 * @file ShadowDOM CSS for the Crontab component
 */

import { css } from "lit";

export const styles = css`
    :host {
        background-color: var(--ak-crontab--BackgroundColor);
        word-break: var(--ak-crontab--WordBreak);
        text-wrap: balance;
        display: inline-block;
    }

    [part="crontab"] {
        display: flex;
        flex-direction: var(--ak-crontab--Direction);
        gap: var(--ak-crontab--Gap);
    }

    [part="natural"] {
        font-size: var(--ak-crontab--natural--FontSize);
        font-style: var(--ak-crontab--natural--FontStyle);
        color: var(--ak-crontab--natural--Color);
        max-width: var(--ak-crontab--natural--MaxWidth);
    }

    [part="cronstring"] {
        font-size: var(--ak-crontab--crontab--FontSize);
        font-style: var(--ak-crontab--crontab--FontStyle);
        color: var(--ak-crontab--crontab--Color);
    }
`;

export default styles;
