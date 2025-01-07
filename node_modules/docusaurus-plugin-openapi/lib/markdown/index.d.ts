import { ApiPageMetadata, InfoPageMetadata } from "../types";
export declare function createApiPageMD({ title, api: { deprecated, "x-deprecated-description": deprecatedDescription, description, parameters, requestBody, responses, }, }: ApiPageMetadata): string;
export declare function createInfoPageMD({ info: { title, version, description }, }: InfoPageMetadata): string;
