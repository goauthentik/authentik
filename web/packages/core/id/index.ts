/**
 * @file Unique ID utilities.
 */

/**
 * A global ID generator.
 *
 * @singleton
 * @runtime common
 *
 * @category IDs
 */
export class IDGenerator {
    static #sequenceIndex = 0;
    static #elementIndex = 0;

    /**
     * Create a new ID for an HTML element.
     *
     * This ID will be unique for the lifetime of the page and will not be
     * exposed on the `window` object.
     *
     * @param name An optional name to use for the element.
     */
    static elementID(name?: string | number): string {
        name = name || ++this.#elementIndex;

        return "«ak-" + name + "»";
    }

    /**
     * Create a new ID.
     */
    static next(): number {
        this.#sequenceIndex += 1;

        return this.#sequenceIndex;
    }

    /**
     * Generate a random ID in hexadecimal format.
     */
    static randomID(characterLength = 6): string {
        const bytes = crypto.getRandomValues(new Uint8Array(characterLength / 2));

        return Array.from(bytes, (a) => a.toString(16)).join("");
    }
}
