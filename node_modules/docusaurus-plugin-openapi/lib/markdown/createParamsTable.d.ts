import { ApiItem } from "../types";
interface Props {
    parameters: ApiItem["parameters"];
    type: "path" | "query" | "header" | "cookie";
}
export declare function createParamsTable({ parameters, type }: Props): string | undefined;
export {};
