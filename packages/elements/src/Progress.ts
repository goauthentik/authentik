import {
    akProgress,
    Progress,
    type ProgressProps,
    type ProgressSeverity,
    type ProgressSize,
    type ProgressVariant,
} from "./impl/Progress/Progress.js";

export { akProgress, Progress, type ProgressProps, type ProgressSeverity, type ProgressSize, type ProgressVariant };

window.customElements.define("ak-progress", Progress);

declare global {
    interface HTMLElementTagNameMap {
        "ak-progress": Progress;
    }
}
