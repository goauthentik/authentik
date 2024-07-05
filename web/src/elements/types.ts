import { AKElement } from "@goauthentik/elements/Base";

import { ReactiveControllerHost } from "lit";

export type ReactiveElementHost<T = AKElement> = Partial<ReactiveControllerHost> & T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Constructor<T = object> = new (...args: any[]) => T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type AbstractConstructor<T = object> = abstract new (...args: any[]) => T;
