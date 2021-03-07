import { Challenge } from ".";

export interface Error {
    code: string;
    string: string;
}

export interface ErrorDict {
    [key: string]: Error[];
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

export enum FlowDesignation {
    Authentication = "authentication",
    Authorization = "authorization",
    Invalidation = "invalidation",
    Enrollment = "enrollment",
    Unrenollment = "unenrollment",
    Recovery = "recovery",
    StageConfiguration = "stage_configuration",
}
