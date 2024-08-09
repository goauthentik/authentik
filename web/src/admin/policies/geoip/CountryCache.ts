import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";

import { DetailedCountry, PoliciesApi } from "@goauthentik/api";

class CountryCache {
    countries: DetailedCountry[];
    lastReceivedAt?: number;
    TTL: number;

    constructor() {
        this.countries = [];
        this.lastReceivedAt = undefined;
        // 1 minute
        this.TTL = 60 * 1000;
    }

    async getCountries() {
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
