/**
 * @file PatternFly constants.
 */

/**
 * Possible dispositions (i.e. color modifiers) for PatternFly components.
 */
export const P4Disposition = {
    Error: "error",
    Warning: "warning",
    Info: "info",
    Neutral: "neutral",
} as const;

export type P4Disposition = (typeof P4Disposition)[keyof typeof P4Disposition];
