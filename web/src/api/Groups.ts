export class Group {

    group_uuid: string;
    name: string;
    is_superuser: boolean;
    attributes: object;
    parent?: Group;

    constructor() {
        throw Error();
    }

}
