/**
 * @file Text measurement utilities.
 */

/**
 * Measures text dimensions using an offscreen canvas.
 */
export class TextMeasurer implements Disposable {
    #ctx: OffscreenCanvasRenderingContext2D | null;

    public get canvas(): OffscreenCanvas | null {
        return this.#ctx?.canvas ?? null;
    }

    public get font(): string | null {
        return this.#ctx?.font ?? null;
    }

    public set font(value: string) {
        if (!this.#ctx) return;

        this.#ctx!.font = value;
    }

    constructor(canvas: OffscreenCanvas = new OffscreenCanvas(300, 150)) {
        this.#ctx = canvas.getContext("2d");

        if (!this.#ctx) {
            console.error("failed to get canvas context");
        }

        const styles = window.getComputedStyle(document.body);

        this.font = `${styles.fontSize} monospace`;
    }

    public measure(text: string): TextMetrics {
        if (!this.#ctx) {
            throw new TypeError("CanvasRenderingContext2D is null");
        }
        return this.#ctx.measureText(text);
    }

    public [Symbol.dispose](): void {
        this.#ctx = null;
    }
}
