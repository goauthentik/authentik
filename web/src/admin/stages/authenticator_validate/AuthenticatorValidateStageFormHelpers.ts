import { aki } from "#common/api/client";

import { DualSelectPair } from "#elements/ak-dual-select/types";

import { deviceTypeRestrictionPair } from "#admin/stages/authenticator_webauthn/utils";

import { Stage, StagesApi } from "@goauthentik/api";

const stageToSelect = (stage: Stage) => [stage.pk, `${stage.name} (${stage.verboseName})`];

export async function stagesProvider(page = 1, search = "") {
    const stages = await aki(StagesApi).stagesAllList({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: stages.pagination,
        options: stages.results.map(stageToSelect),
    };
}

export function stagesSelector(instanceStages: string[] | undefined) {
    if (!instanceStages) {
        return async (stages: DualSelectPair<Stage>[]) =>
            stages.filter(([_0, _1, _2, stage]: DualSelectPair<Stage>) => stage !== undefined);
    }
    return async () => {
        const stagesApi = aki(StagesApi);
        const stages = await Promise.allSettled(
            instanceStages.map((instanceId) =>
                stagesApi.stagesAllRetrieve({ stageUuid: instanceId }),
            ),
        );
        return stages
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(stageToSelect);
    };
}

export async function authenticatorWebauthnDeviceTypesListProvider(page = 1, search = "") {
    const devicetypes = await aki(StagesApi).stagesAuthenticatorWebauthnDeviceTypesList({
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: devicetypes.pagination,
        options: devicetypes.results.map(deviceTypeRestrictionPair),
    };
}
