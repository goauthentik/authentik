import { DEFAULT_CONFIG } from "#common/api/config";

import { DetailedCountry, PoliciesApi } from "@goauthentik/api";

class CountryCache {
    protected countries: DetailedCountry[];
    protected lastReceivedAt?: number;
    protected TTL: number;

    public constructor() {
        this.countries = [];
        this.lastReceivedAt = undefined;
        // 1 minute
        this.TTL = 60 * 1000;
    }

    public async getCountries() {
        const shouldInvalidate =
            this.lastReceivedAt === undefined ||
            new Date().getTime() - this.lastReceivedAt > this.TTL;

        if (!shouldInvalidate) {
            return this.countries;
        }

        await new PoliciesApi(DEFAULT_CONFIG).policiesGeoipIso3166List().then((response) => {
            this.countries = response;
            this.lastReceivedAt = new Date().getTime();
        });

        return this.countries;
    }
}

export const countryCache = new CountryCache();
