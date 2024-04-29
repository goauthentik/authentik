import type { TemplateResult } from "lit";

export type SearchTuple = [string, string, undefined | string | TemplateResult];
export type SearchGroup = { name: string; options: SearchTuple[] };

export type GroupedOptions =
    | {
          grouped: false;
          options: SearchTuple[];
      }
    | {
          grouped: true;
          options: SearchGroup[];
      };

export type SearchOptions = SearchTuple[] | GroupedOptions;
