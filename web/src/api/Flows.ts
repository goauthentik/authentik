import { ChallengeChoices } from "authentik-api";

export interface Error {
    code: string;
    string: string;
}

export interface ErrorDict {
    [key: string]: Error[];
}
