/**
 * @file Width measurement for truncation.
 *
 * The default {@link characterMeasurer} counts characters, keeping the
 * truncation algorithms pure and SSR-safe. DOM callers pass a measurer built
 * from {@link createCanvasMeasurer} to fit a real rendered pixel width.
 */

/**
 * A cost function: how wide is `text`, in whatever unit the caller cares about.
 */
export type Measurer = (text: string) => number;

export type CanvasLike = OffscreenCanvas | HTMLCanvasElement;

type CanvasContext = CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D;

/**
 * The default measurer: one unit per character.
 */
export function characterMeasurer(text: string): number {
    return text.length;
}

/**
 * Build a measurer backed by a canvas 2D context's `measureText`.
 *
 * Not unit-tested — it is a thin wrapper over the platform `measureText`. A
 * single `OffscreenCanvas` may be shared across many measurers.
 *
 * @param canvas The canvas whose 2D context measures the text.
 * @param font A CSS font shorthand, e.g. `"14px monospace"`.
 */
export function createCanvasMeasurer(canvas: CanvasLike, font: string): Measurer {
    const ctx = canvas.getContext("2d") as CanvasContext | null;

    if (!ctx) {
        throw new Error("truncator: failed to acquire a 2D canvas context");
    }

    ctx.font = font;

    return (text) => ctx.measureText(text).width;
}
