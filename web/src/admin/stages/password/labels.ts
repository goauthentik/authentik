import { MessageFormatter } from "#common/ui/locale/format";

import { CheckboxItem } from "#elements/ak-checkbox-group/ak-checkbox-group";

import { BackendsEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";

export const BackendLabelRecord: Record<BackendsEnum, MessageFormatter<string>> = {
    [BackendsEnum.AuthentikCoreAuthInbuiltBackend]: () => msg("User database + standard password"),
    [BackendsEnum.AuthentikCoreAuthTokenBackend]: () => msg("User database + app passwords"),
    [BackendsEnum.AuthentikSourcesLdapAuthLdapBackend]: () => msg("User database + LDAP password"),
    [BackendsEnum.AuthentikSourcesKerberosAuthKerberosBackend]: () =>
        msg("User database + Kerberos password"),
    [BackendsEnum.UnknownDefaultOpenApi]: () => msg("Unknown backend"),
};

export const BackendCheckboxItems: CheckboxItem<BackendsEnum>[] = [
    BackendsEnum.AuthentikCoreAuthInbuiltBackend,
    BackendsEnum.AuthentikCoreAuthTokenBackend,
    BackendsEnum.AuthentikSourcesLdapAuthLdapBackend,
    BackendsEnum.AuthentikSourcesKerberosAuthKerberosBackend,
].map((backend) => ({
    name: backend,
    label: BackendLabelRecord[backend](),
}));
