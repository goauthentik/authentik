/**
 * @file Global constants used throughout the application.
 *
 * @todo Much of this content can be moved to a specific file, element, or component.
 */

/// <reference types="../../types/esbuild.js" />

// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { AKEnterpriseRefreshEvent, AKRefreshEvent } from "#common/events";

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

/**
 * Event name for refresh events.
 *
 * @deprecated Use {@linkcode AKRefreshEvent}
 */
export const EVENT_REFRESH = "ak-refresh";

/**
 * Event name for enterprise refresh events.
 *
 * @deprecated Use {@linkcode AKEnterpriseRefreshEvent}
 */
export const EVENT_REFRESH_ENTERPRISE = "ak-refresh-enterprise";

//#endregion

//#region LocalStorage

export const LOCALSTORAGE_AUTHENTIK_KEY = "authentik-local-settings";

//#endregion
