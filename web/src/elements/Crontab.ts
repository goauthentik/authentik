/**
 * @file Barrel file and default registry ('ak-crontab') for the Crontab component
 */

import { akCrontab, Crontab, type CrontabProps } from "./Crontab_impl/Crontab";

export { akCrontab, Crontab };
export type { CrontabProps };

window.customElements.define("ak-crontab", Crontab);

declare global {
    interface HTMLElementTagNameMap {
        "ak-crontab": Crontab;
    }
}
