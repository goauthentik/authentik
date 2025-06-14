import type {
    GroupedOptions,
    SelectGrouped,
    SelectOption,
    SelectOptions,
} from "@goauthentik/elements/types.js";

type Pair = [string, SelectOption];
const mapPair = (option: SelectOption): Pair => [option[0], option];

const isSelectOptionsArray = (v: unknown): v is SelectOption[] => Array.isArray(v);

// prettier-ignore
const isGroupedOptionsCollection = (v: unknown): v is SelectGrouped =>
    v !== null && typeof v === "object" && "grouped" in v && v.grouped === true;

export const groupOptions = (options: SelectOptions): GroupedOptions =>
    isSelectOptionsArray(options) ? { grouped: false, options: options } : options;

export function optionsToFlat(groupedOptions: GroupedOptions): Pair[] {
    return isGroupedOptionsCollection(groupedOptions)
        ? groupedOptions.options.reduce(
              (acc: Pair[], { options }): Pair[] => [...acc, ...options.map(mapPair)],
              [] as Pair[],
          )
        : groupedOptions.options.map(mapPair);
}

export function findFlatOptions(options: Pair[], value: string): Pair[] {
    const fragLength = value.length;
    return options.filter((option) => (option[1][1] ?? "").substring(0, fragLength) === value);
}

export function findOptionsSubset(
    groupedOptions: GroupedOptions,
    value: string,
    caseSensitive = false,
): GroupedOptions {
    const fragLength = value.length;
    if (value.trim() === "") {
        return groupedOptions;
    }

    const compValue = caseSensitive ? value : value.toLowerCase();
    const compOption = (option: SelectOption) => {
        const extractedOption = (option[1] ?? "").substring(0, fragLength);
        return caseSensitive ? extractedOption : extractedOption.toLowerCase();
    };

    const optFilter = (options: SelectOption[]) =>
        options.filter((option) => compOption(option) === compValue);

    return groupedOptions.grouped
        ? {
              grouped: true,
              options: groupedOptions.options
                  .map(({ name, options }) => ({
                      name,
                      options: optFilter(options),
                  }))
                  .filter(({ options }) => options.length !== 0),
          }
        : {
              grouped: false,
              options: optFilter(groupedOptions.options),
          };
}
