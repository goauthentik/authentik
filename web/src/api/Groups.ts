import { EventContext } from "./Events";

export class Group {

    group_uuid: string;
    name: string;
    is_superuser: boolean;
    attributes: EventContext;
    parent?: Group;

    constructor() {
        throw Error();
    }

}
