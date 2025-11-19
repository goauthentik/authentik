import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { IDGenerator } from "@goauthentik/core/id";

import { capitalCase } from "change-case";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const dictionaries = join(__dirname, "dictionaries");

function simpleHash(seed: string) {
    let hash = 0;

    for (let i = 0; i < seed.length; i++) {
        hash = (hash * 31 + seed.charCodeAt(i)) | 0; // keep it 32-bit
    }
    return Math.abs(hash);
}

class LazyDictionary {
    #entries: string[] = [];
    #filePath: string;
    #loaded = false;

    constructor(filePath: string) {
        this.#filePath = filePath;
    }

    public load() {
        if (this.#loaded) return;

        this.#entries = readFileSync(this.#filePath, "utf8").split("\n").filter(Boolean);
        this.#loaded = true;

        return this.#entries;
    }

    public random(seed: string) {
        this.load();

        // We use modulo to ensure that the seed is always within the range of the dictionary
        const index = Math.floor(simpleHash(seed) % this.#entries.length);

        return this.#entries[index];
    }
}

const Adjectives = new LazyDictionary(join(dictionaries, "adjectives.txt"));
const Colors = new LazyDictionary(join(dictionaries, "colors.txt"));

/**
 * Generate a random phrase consisting of an two adjectives and a color.
 *
 * @param seeds Seeds to use for the random number generator.
 */
export function randomPhrases(...seeds: string[]) {
    const [
        adjectiveSeed1 = IDGenerator.randomID(),
        adjectiveSeed2 = IDGenerator.randomID(),
        // Ensure a pairing of the first adjective and color is always used
        // allow for a more predictable result.
        colorSeed = adjectiveSeed1,
    ] = seeds;

    const adjective1 = Adjectives.random(adjectiveSeed1);
    const adjective2 = Adjectives.random(adjectiveSeed2);
    const color = Colors.random(colorSeed);

    return [adjective1, adjective2, color];
}

/**
 * Generate a random name consisting of an adjective, a color, and a phrase.
 *
 * @param seeds Seeds to use for the random number generator.
 */
export function randomName(...seeds: string[]) {
    return capitalCase(randomPhrases(...seeds).join(" "));
}
