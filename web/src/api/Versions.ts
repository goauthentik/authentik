import { DefaultClient } from "./Client";

export class Version {

    version_current: string;
    version_latest: string;
    outdated: boolean;

    constructor() {
        throw Error();
    }

    static get(): Promise<Version> {
        return DefaultClient.fetch<Version>(["admin", "version"]);
    }

    toString(): string {
        return this.version_current;
    }

}
