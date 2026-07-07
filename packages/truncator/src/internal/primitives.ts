/**
 * @file Shared truncation primitives.
 */

import { characterMeasurer, type Measurer } from "../measurer.js";

export interface TruncateOptions {
    /**
     * Budget, in measurer units.
     */
    maxWidth: number;
    /**
     * Defaults to characterMeasurer.
     */
    measure?: Measurer;
    /**
     * Defaults to "…".
     */
    ellipsis?: string;
}

/**
 * A measurement of head and tail segments, to track how many segments are kept on each side.
 */
type Measurement = [head: number, tail: number];

/**
 * A reducer function that returns a truncated string.
 */
export type Truncator = (input: string, options: TruncateOptions) => string;

/**
 * Resolve truncation options, filling in defaults.
 */
function resolve(options: TruncateOptions) {
    return {
        maxWidth: options.maxWidth,
        measure: options.measure ?? characterMeasurer,
        ellipsis: options.ellipsis ?? "…",
    };
}

/**
 * Keep the head, drop the tail: `"keep head…"`. The universal fallback.
 */
export function endEllipsis(input: string, options: TruncateOptions): string {
    const { maxWidth, measure, ellipsis } = resolve(options);

    if (measure(input) <= maxWidth) return input;
    if (measure(ellipsis) > maxWidth) return ellipsis;

    let head = "";

    for (const ch of input) {
        if (measure(head + ch + ellipsis) > maxWidth) break;
        head += ch;
    }

    return head + ellipsis;
}

export interface MiddleEllipsisConfig {
    /**
     * 0..1, weight toward head growth (default 0.5)
     */
    headBias?: number;
}

/**
 * Keep head + tail with the ellipsis in the middle, grown greedily from both
 * ends under the measurer. `headBias` (0..1) weights growth toward the head.
 */
export function middleEllipsis(
    input: string,
    options: TruncateOptions,
    config: MiddleEllipsisConfig = {},
): string {
    const { maxWidth, measure, ellipsis } = resolve(options);

    if (measure(input) <= maxWidth) return input;
    if (measure(ellipsis) > maxWidth) return ellipsis;

    const headBias = config.headBias ?? 0.5;
    const chars = Array.from(input);

    const fits = (h: number, t: number) =>
        measure(chars.slice(0, h).join("") + ellipsis + chars.slice(chars.length - t).join("")) <=
        maxWidth;

    let head = 0;
    let tail = 0;

    while (head + tail < chars.length) {
        const growHead = head / Math.max(1, head + tail) < headBias;

        if (growHead && fits(head + 1, tail)) head++;
        else if (growHead && fits(head, tail + 1)) tail++;
        else if (!growHead && fits(head, tail + 1)) tail++;
        else if (!growHead && fits(head + 1, tail)) head++;
        else break;
    }

    if (head === 0 && tail === 0) {
        return ellipsis;
    }

    return chars.slice(0, head).join("") + ellipsis + chars.slice(chars.length - tail).join("");
}

/**
 * Keep whole leading and trailing segments, dropping middle ones,
 * with a single ellipsis segment between, re-joined by `separator`.
 *
 * Falls back to character middle-ellipsis on the joined string when there are
 * too few segments or even the 1-head/1-tail form won't fit.
 */
export function segmentEllipsis(
    segments: string[],
    separator: string,
    options: TruncateOptions,
    config: MiddleEllipsisConfig = {},
): string {
    const { maxWidth, measure, ellipsis } = resolve(options);
    const joined = segments.join(separator);

    if (measure(joined) <= maxWidth) {
        return joined;
    }

    if (segments.length >= 3) {
        const headBias = config.headBias ?? 0.5;

        const build = (h: number, t: number) =>
            [...segments.slice(0, h), ellipsis, ...segments.slice(segments.length - t)].join(
                separator,
            );

        if (measure(build(1, 1)) <= maxWidth) {
            let head = 1;
            let tail = 1;

            while (head + tail < segments.length) {
                const growHead = head / (head + tail) < headBias;

                const primary: Measurement = growHead ? [head + 1, tail] : [head, tail + 1];

                const secondary: Measurement = growHead ? [head, tail + 1] : [head + 1, tail];

                if (measure(build(primary[0], primary[1])) <= maxWidth) {
                    [head, tail] = primary;
                } else if (measure(build(secondary[0], secondary[1])) <= maxWidth) {
                    [head, tail] = secondary;
                } else {
                    break;
                }
            }

            return build(head, tail);
        }
    }

    return middleEllipsis(joined, options, config);
}

/**
 * Run structure-aware reducers in priority order, re-measuring after each,
 * and stop the moment the input fits.
 *
 * @returns the last result even if still over budget (callers should end their reducer list with a guaranteed hard cut).
 */
export function reducePipeline(
    input: string,
    options: TruncateOptions,
    reducers: Truncator[],
): string {
    const { maxWidth, measure } = resolve(options);

    let current = input;

    if (measure(current) <= maxWidth) {
        return current;
    }

    for (const reducer of reducers) {
        current = reducer(current, options);

        if (measure(current) <= maxWidth) {
            return current;
        }
    }

    return current;
}
