import { MediaTypeObject } from "../openapi/types";
interface Props {
    style?: any;
    title: string;
    body: {
        content?: {
            [key: string]: MediaTypeObject;
        };
        description?: string;
        required?: boolean;
    };
    type: "request" | "response";
}
export declare function createSchemaTable({ title, body, type, ...rest }: Props): string | undefined;
export {};
