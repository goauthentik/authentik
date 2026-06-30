import { globalAK } from "#common/global";
import { ascii_letters, digits, randomString } from "#common/utils";

import { Broadcast } from "#flow/tabs/broadcast";
import { AKMultiTabExitEvent } from "#flow/tabs/events";
import { TabID } from "#flow/tabs/TabID";

import { ConsoleLogger } from "#logger/browser";

/**
 * Multi-tab continuous-login coordination.
 *
 * When several tabs sit in the same flow (e.g. multiple SP-initiated SAML logins), only one needs
 * the user to authenticate. The tab that completes auth becomes the "leader" and walks every other
 * ("follower") tab through its own resume, one at a time:
 *
 *  1. The leader takes a cross-tab lock ({@link lockKey} in localStorage) so a second finishing tab
 *     won't also start resuming — it suppresses its own exit and bows out.
 *  2. For each discovered follower the leader mints a one-shot `resumeID`, starts waiting for that
 *     tab's exit, then tells it to continue ({@link Broadcast.resumeTab}).
 *  3. The follower stores the `resumeID`, re-enters its flow, and only echoes it back in an exit
 *     event once it reaches its OWN final redirect (see `final_redirect` / RedirectStage). The
 *     leader matches tabID + resumeID, so stale or out-of-order exits from earlier rounds are
 *     ignored.
 *  4. {@link waitForTabExit} bounds the wait so one stuck follower can't deadlock the leader.
 *
 * Resume is only ever started from a `final_redirect` challenge — the terminal redirect out of a
 * completed auth flow — never from intermediate hops (source stages, the same-origin SAML re-entry).
 */

const lockKey = "authentik-tab-locked";
const logger = ConsoleLogger.prefix("mtab/orchestrate");

// How often to poll for a follower that hasn't sent its exit event yet.
const TAB_EXIT_TIMEOUT_MS = 3000;
// Hard ceiling on waiting for a single follower, so one stuck tab can't block the leader forever.
const TAB_EXIT_MAX_WAIT_MS = 15000;
// Grace period after an exit event before resolving, to let the follower's navigation settle.
const TAB_EXIT_SETTLE_MS = 100;

export function multiTabOrchestrateLeave() {
    Broadcast.shared.dispatchExit();
    TabID.shared.clear();
}

export function suppressNextExitForSameOriginNavigation() {
    Broadcast.shared.suppressNextExit();
}

/**
 * Wait for a tab to exit, with a timeout and fallback to checking if the tab is still present.
 *
 * @param tabID The tab ID to wait for.
 * @param resumeID The resume ID to wait for.
 *
 * @returns A promise that resolves when the tab has exited or the timeout has been reached.
 */
function waitForTabExit(tabID: string, resumeID: string): Promise<void> {
    const { resolve, promise } = Promise.withResolvers<void>();
    const start = Date.now();

    let timeout = -1;
    let finished = false;
    const abort = new AbortController();

    const cleanup = (delay = 0) => {
        if (finished) {
            return;
        }

        finished = true;

        self.clearTimeout(timeout);
        abort.abort();

        self.setTimeout(() => {
            resolve();
        }, delay);
    };

    const exitListener = ({ tabID: eventTabID, resumeID: eventResumeID }: AKMultiTabExitEvent) => {
        if (eventTabID !== tabID || eventResumeID !== resumeID) {
            return;
        }

        logger.debug("tab exited", tabID);

        cleanup(TAB_EXIT_SETTLE_MS);
    };

    const timeoutCheck = async () => {
        if (Date.now() - start >= TAB_EXIT_MAX_WAIT_MS) {
            logger.warn("Timed out waiting for tab to complete, moving on", tabID);

            cleanup();

            return;
        }

        const tabs = await Broadcast.shared.discoverTabs();

        if (!tabs.has(tabID)) {
            logger.warn("Timed out waiting for tab exit event, tab is gone", tabID);
            cleanup();

            return;
        }

        logger.warn("Timed out waiting for tab to exit, tab still active", tabID);

        timeout = self.setTimeout(timeoutCheck, TAB_EXIT_TIMEOUT_MS);
    };

    window.addEventListener(AKMultiTabExitEvent.eventName, exitListener, { signal: abort.signal });

    timeout = self.setTimeout(timeoutCheck, TAB_EXIT_TIMEOUT_MS);

    return promise;
}

export async function multiTabOrchestrateResume() {
    if (!globalAK().brand.flags.flowsContinuousLogin) {
        return;
    }

    const lockTabID = localStorage.getItem(lockKey);
    const tabs = await Broadcast.shared.discoverTabs();

    logger.debug("Got list of tabs", tabs);

    if (lockTabID && tabs.has(lockTabID)) {
        logger.debug("Tabs locked, suppressing same-origin exit.");
        suppressNextExitForSameOriginNavigation();

        return;
    }

    logger.debug("Locking tabs");
    localStorage.setItem(lockKey, TabID.shared.current);

    for (const tab of tabs) {
        const resumeID = randomString(32, ascii_letters + digits);
        const done = waitForTabExit(tab, resumeID);

        logger.debug("Telling tab to continue", tab);
        Broadcast.shared.resumeTab(tab, resumeID);

        await done;

        logger.debug("Tab done, continuing", tab);
    }

    logger.debug("All tabs done.");
    localStorage.removeItem(lockKey);
}
