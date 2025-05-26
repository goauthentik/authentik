/**
 * @file Global constants used throughout the application.
 *
 * @todo Much of this content can be moved to a specific file, element, or component.
 */

/// <reference types="../../types/esbuild.js" />

//#region Patternfly

export const SECONDARY_CLASS = "pf-m-secondary";
export const SUCCESS_CLASS = "pf-m-success";
export const ERROR_CLASS = "pf-m-danger";
export const PROGRESS_CLASS = "pf-m-in-progress";
export const CURRENT_CLASS = "pf-m-current";

//#endregion

//#region Application

/**
 * The delimiter used to parse the URL for the current route.
 *
 * @todo Move this to the ak-router.
 */
export const ROUTE_SEPARATOR = ";";

//#endregion

//#region Events

export const EVENT_REFRESH = "ak-refresh";
export const EVENT_NOTIFICATION_DRAWER_TOGGLE = "ak-notification-toggle";
export const EVENT_API_DRAWER_TOGGLE = "ak-api-drawer-toggle";
export const EVENT_FLOW_INSPECTOR_TOGGLE = "ak-flow-inspector-toggle";
export const EVENT_WS_MESSAGE = "ak-ws-message";
export const EVENT_FLOW_ADVANCE = "ak-flow-advance";
export const EVENT_LOCALE_CHANGE = "ak-locale-change";
export const EVENT_LOCALE_REQUEST = "ak-locale-request";
export const EVENT_REQUEST_POST = "ak-request-post";
export const EVENT_MESSAGE = "ak-message";
export const EVENT_THEME_CHANGE = "ak-theme-change";
export const EVENT_REFRESH_ENTERPRISE = "ak-refresh-enterprise";

//#endregion

//#region WebSocket

export const WS_MSG_TYPE_MESSAGE = "message";
export const WS_MSG_TYPE_REFRESH = "refresh";

//#endregion

//#region LocalStorage

export const LOCALSTORAGE_AUTHENTIK_KEY = "authentik-local-settings";

//#endregion
