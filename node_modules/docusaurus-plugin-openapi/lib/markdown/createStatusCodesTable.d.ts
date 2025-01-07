import { ApiItem } from "../types";
interface Props {
    responses: ApiItem["responses"];
}
export declare function createStatusCodesTable({ responses }: Props): string | undefined;
export {};
