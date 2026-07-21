import { open } from "node:fs/promises";

/** Pmtiles Source backed by a local file handle. */
export class NodeFileSource {
    #path;
    #handle;

    constructor(path) {
        this.#path = path;
    }

    getKey() {
        return this.#path;
    }

    async getBytes(offset, length) {
        this.#handle ??= await open(this.#path, "r");
        const buffer = Buffer.alloc(length);
        await this.#handle.read(buffer, 0, length, offset);
        return { data: buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + length) };
    }

    async close() {
        await this.#handle?.close();
    }
}
