import { IDGenerator } from "@goauthentik/core/id";

import {
    adjectives,
    colors,
    Config as NameConfig,
    uniqueNamesGenerator,
} from "unique-names-generator";

/**
 * Given a dictionary of words, slice the dictionary to only include words that start with the given letter.
 */
export function alliterate(dictionary: string[], letter: string): string[] {
    let firstIndex = 0;

    for (let i = 0; i < dictionary.length; i++) {
        if (dictionary[i][0] === letter) {
            firstIndex = i;
            break;
        }
    }

    let lastIndex = firstIndex;

    for (let i = firstIndex; i < dictionary.length; i++) {
        if (dictionary[i][0] !== letter) {
            lastIndex = i;
            break;
        }
    }

    return dictionary.slice(firstIndex, lastIndex);
}

export function createRandomName({
    seed = IDGenerator.randomID(),
    ...config
}: Partial<NameConfig> = {}) {
    const randomLetterIndex =
        typeof seed === "number"
            ? seed
            : Array.from(seed).reduce((acc, char) => acc + char.charCodeAt(0), 0);

    const letter = adjectives[randomLetterIndex % adjectives.length][0];

    const availableAdjectives = alliterate(adjectives, letter);

    const availableColors = alliterate(colors, letter);

    const name = uniqueNamesGenerator({
        dictionaries: [availableAdjectives, availableAdjectives, availableColors],
        style: "capital",
        separator: " ",
        length: 3,
        seed,
        ...config,
    });

    return name;
}
