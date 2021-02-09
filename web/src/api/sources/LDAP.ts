import { DefaultClient } from "../Client";
import { Source } from "../Sources";

export class LDAPSource extends Source {
    server_uri: string;
    bind_cn: string;
    start_tls: boolean
    base_dn: string;
    additional_user_dn: string;
    additional_group_dn: string;
    user_object_filter: string;
    group_object_filter: string;
    group_membership_field: string;
    object_uniqueness_field: string;
    sync_users: boolean;
    sync_users_password: boolean;
    sync_groups: boolean;
    sync_parent_group?: string;
    property_mappings: string[];
    property_mappings_group: string[];

    constructor() {
        super();
        throw Error();
    }

    static get(slug: string): Promise<LDAPSource> {
        return DefaultClient.fetch<LDAPSource>(["sources", "ldap", slug]);
    }

    static syncStatus(slug: string): Promise<{ last_sync?: number }> {
        return DefaultClient.fetch(["sources", "ldap", slug, "sync_status"]);
    }

}
