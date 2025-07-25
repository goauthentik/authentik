import { toUserRoute } from "#elements/router/navigation";

type SettingPageTab = "sources" | "mfa" | "details";

export const toUserSettings = (params?: { page: SettingPageTab }) => {
    return toUserRoute("settings", params);
};
