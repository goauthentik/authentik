/**
 * @file Label kinds and their reveal zooms.
 *
 * These are the contract between the bundled hexworld archive and the style
 * that renders it: the generator stamps each place feature with a minzoom
 * derived from {@linkcode LABEL_MIN_ZOOM}, and the runtime style gates the
 * matching layer on the same number. `packages/geo` imports this module so
 * the two cannot drift — see that package's README.
 */

export const LabelKinds = new Set(["country", "region", "locality"] as const);
export type LabelKind = typeof LabelKinds extends Set<infer K> ? K : never;

/** Zoom at which each kind of label first appears. */
export const LABEL_MIN_ZOOM: Record<LabelKind, number> = {
    country: 0,
    region: 3,
    locality: 6,
};

/** Text size, in px, per label kind. */
export const LABEL_TEXT_SIZE: Record<LabelKind, number> = {
    country: 16,
    region: 13,
    locality: 11,
};
