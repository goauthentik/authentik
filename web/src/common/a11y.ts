/**
 * @file Accessibility utilities.
 */

import { createMediaQueryEffect } from "#common/matchers";

//#region Constants

/**
 * Class names applied to the document element based on user accessibility preferences.
 *
 * @category Accessibility
 */
export const A11YClassName = {
    ReduceMotion: "ak-m-reduce-motion",
    ReduceTransparency: "ak-m-reduce-transparency",
    MoreContrast: "ak-m-more-contrast",
    LessContrast: "ak-m-less-contrast",
} as const;

export type A11YClassName = (typeof A11YClassName)[keyof typeof A11YClassName];

//#endregion

//#region Effects

/**
 * Create an effect that applies the user's motion preference to the document.
 *
 * ```ts
 * const dispose = createMotionPreferenceEffect();
 * ```
 *
 * @category Accessibility
 */
export function createMotionPreferenceEffect() {
    const dispose = createMediaQueryEffect(
        "(prefers-reduced-motion: reduce)",
        (event) => {
            document.documentElement.classList.toggle(A11YClassName.ReduceMotion, event.matches);
        },
        {
            immediate: true,
        },
    );

    return dispose;
}

/**
 * Create an effect that applies the user's motion preference to the document.
 *
 * ```ts
 * const dispose = createMotionPreferenceEffect();
 * ```
 *
 * @category Accessibility
 */
export function createContrastPreferenceEffect() {
    const dispose = createMediaQueryEffect(
        "(prefers-contrast: more)",
        (event) => {
            document.documentElement.classList.toggle(A11YClassName.MoreContrast, event.matches);
        },
        {
            immediate: true,
        },
    );

    return dispose;
}

/**
 * Create an effect that applies the user's motion preference to the document.
 *
 * ```ts
 * const dispose = createMotionPreferenceEffect();
 * ```
 *
 * @category Accessibility
 */
export function createTransparencyPreferenceEffect() {
    const dispose = createMediaQueryEffect(
        "(prefers-reduced-transparency: reduce)",
        (event) => {
            document.documentElement.classList.toggle(
                A11YClassName.ReduceTransparency,
                event.matches,
            );
        },
        {
            immediate: true,
        },
    );

    return dispose;
}

//#endregion

//#region Predicates

/**
 * Predicate to determine if the user agent indicates a preference for reduced motion.
 *
 * ```ts
 * const prefersReducedMotion = isReducedMotionPreferred();
 * ```
 *
 * @category Accessibility
 */
export function isReducedMotionPreferred(): boolean {
    return document.documentElement.classList.contains(A11YClassName.ReduceMotion);
}

/**
 * Predicate to determine if the user agent indicates a preference for reduced transparency.
 *
 * ```ts
 * const prefersReducedTransparency = isReducedTransparencyPreferred();
 * ```
 *
 * @category Accessibility
 */
export function isReducedTransparencyPreferred(): boolean {
    return document.documentElement.classList.contains(A11YClassName.ReduceTransparency);
}

/**
 * Predicate to determine if the user agent indicates a preference for more contrast.
 *
 * ```ts
 * const prefersMoreContrast = isMoreContrastPreferred();
 * ```
 *
 * @category Accessibility
 */
export function isMoreContrastPreferred(): boolean {
    return document.documentElement.classList.contains(A11YClassName.MoreContrast);
}

//#endregion
