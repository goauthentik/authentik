/**
 * @file PatternFly constants.
 */

/**
 * Possible dispositions (i.e. color modifiers) for PatternFly components.
 */
export const P4Disposition = {
    Error: "error",
    Warning: "warning",
    Danger: "danger",
    Info: "info",
    Neutral: "neutral",
} as const;

export type P4Disposition = (typeof P4Disposition)[keyof typeof P4Disposition];

export const P4BannerDispositionIconClassName = {
    [P4Disposition.Info]: "fas fa-info-circle",
    [P4Disposition.Warning]: "fas fa-exclamation-triangle",
    [P4Disposition.Danger]: "fas fa-exclamation-triangle",
    [P4Disposition.Neutral]: "fas fa-times",
    [P4Disposition.Error]: "fas fa-times",
} as const satisfies Record<P4Disposition, string>;

export const P4BannerDispositionClassName = {
    [P4Disposition.Info]: "pf-m-info",
    [P4Disposition.Warning]: "pf-m-warning",
    [P4Disposition.Danger]: "pf-m-danger",
    [P4Disposition.Neutral]: "pf-m-gray",
    [P4Disposition.Error]: "pf-m-error",
} as const satisfies Record<P4Disposition, string>;
