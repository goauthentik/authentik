import type { SearchOptions, SearchTuple } from "./types.js";

type Pair = [string, string];
const justThePair = ([key, label]: SearchTuple): Pair => [key, label];

export function optionsToOptionsMap(options: SearchOptions): Map<string, string> {
    const pairs: Pair[] = Array.isArray(options)
        ? options.map(justThePair)
        : options.grouped
          ? options.options.reduce(
                (acc: Pair[], { options }): Pair[] => [...acc, ...options.map(justThePair)],
                [] as Pair[],
            )
          : options.options.map(justThePair);
    return new Map(pairs);
}
