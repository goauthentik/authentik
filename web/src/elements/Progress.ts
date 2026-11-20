import {
    akProgress,
    Progress,
    type ProgressProps,
    type ProgressSeverity,
    type ProgressSize,
    type ProgressVariant,
} from "./Progress_impl/Progress";

export {
    akProgress,
    Progress,
    type ProgressProps,
    type ProgressSeverity,
    type ProgressSize,
    type ProgressVariant,
};

customElements.define("ak-progress", Progress);

declare global {
    interface HTMLElementTagNameMap {
        "ak-progress": Progress;
    }
}
