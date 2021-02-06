import { DefaultClient } from "../Client";
import { Provider } from "../Providers";

export class ProxyProvider extends Provider {
    internal_host: string;
    external_host: string;
    internal_host_ssl_validation: boolean
    certificate?: string;
    skip_path_regex: string;
    basic_auth_enabled: boolean;
    basic_auth_password_attribute: string;
    basic_auth_user_attribute: string;

    constructor() {
        super();
        throw Error();
    }

    static get(id: number): Promise<ProxyProvider> {
        return DefaultClient.fetch<ProxyProvider>(["providers", "proxy", id.toString()]);
    }

    static getMetadata(id: number): Promise<{ metadata: string }> {
        return DefaultClient.fetch(["providers", "proxy", id.toString(), "metadata"]);
    }

    static appUrl(rest: string): string {
        return `/application/proxy/${rest}`;
    }
}
