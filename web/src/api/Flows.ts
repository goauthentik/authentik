import { ChallengeTypeEnum } from "authentik-api";

export interface Error {
    code: string;
    string: string;
}

export interface ErrorDict {
    [key: string]: Error[];
}

export interface Challenge {
    type: ChallengeTypeEnum;
    component?: string;
    title?: string;
    response_errors?: ErrorDict;
}

export interface WithUserInfoChallenge extends Challenge {
    pending_user: string;
    pending_user_avatar: string;
}

export interface ShellChallenge extends Challenge {
    body: string;
}

export interface RedirectChallenge extends Challenge {
    to: string;
}
