import { globalAK } from "#common/global";
import { ascii_letters, digits, randomString } from "#common/utils";

import { Broadcast, BroadcastExitEventDetail } from "#flow/tabs/broadcast";
import { TabID } from "#flow/tabs/TabID";

import { ConsoleLogger } from "#logger/browser";

const lockKey = "authentik-tab-locked";
const logger = ConsoleLogger.prefix("mtab/orchestrate");

const TAB_EXIT_TIMEOUT_MS = 3000;
const TAB_EXIT_MAX_WAIT_MS = 15000;
const TAB_EXIT_SETTLE_MS = 100;

export function multiTabOrchestrateLeave() {
    Broadcast.shared.akExitTab();
    TabID.shared.clear();
}

export function multiTabOrchestrateSameOriginNavigation() {
    Broadcast.shared.akSuppressNextExit();
}

async function waitForTabExit(tab: string, resumeID: string) {
    const done = Promise.withResolvers<void>();
    const started = Date.now();

    let timeout = -1;
    let finished = false;
    const abort = new AbortController();

    const finish = (delay = 0) => {
        if (finished) {
            return;
        }
        finished = true;
        self.clearTimeout(timeout);
        abort.abort();
        self.setTimeout(() => {
            done.resolve();
        }, delay);
    };

    const exitListener = (event: Event) => {
        const detail = (event as CustomEvent<BroadcastExitEventDetail>).detail;
        if (detail.tabID !== tab || detail.resumeID !== resumeID) {
            return;
        }
        logger.debug("tab exited", tab);
        finish(TAB_EXIT_SETTLE_MS);
    };

    const timeoutCheck = async () => {
        if (Date.now() - started >= TAB_EXIT_MAX_WAIT_MS) {
            logger.warn("Timed out waiting for tab to complete, moving on", tab);
            finish();
            return;
        }
        const tabs = await Broadcast.shared.akTabDiscover();
        if (!tabs.has(tab)) {
            logger.warn("Timed out waiting for tab exit event, tab is gone", tab);
            finish();
            return;
        }
        logger.warn("Timed out waiting for tab to exit, tab still active", tab);
        timeout = self.setTimeout(timeoutCheck, TAB_EXIT_TIMEOUT_MS);
    };

    window.addEventListener("ak-multitab-exit", exitListener, { signal: abort.signal });
    timeout = self.setTimeout(timeoutCheck, TAB_EXIT_TIMEOUT_MS);

    await done.promise;
}

export async function multiTabOrchestrateResume() {
    if (!globalAK().brand.flags.flowsContinuousLogin) {
        return;
    }

    const lockTabID = localStorage.getItem(lockKey);
    const tabs = await Broadcast.shared.akTabDiscover();

    logger.debug("Got list of tabs", tabs);

    if (lockTabID && tabs.has(lockTabID)) {
        logger.debug("Tabs locked, suppressing same-origin exit.");
        multiTabOrchestrateSameOriginNavigation();
        return;
    }

    logger.debug("Locking tabs");
    localStorage.setItem(lockKey, TabID.shared.current);

    for (const tab of tabs) {
        const resumeID = randomString(32, ascii_letters + digits);
        const done = waitForTabExit(tab, resumeID);

        logger.debug("Telling tab to continue", tab);
        Broadcast.shared.akResumeTab(tab, resumeID);

        await done;

        logger.debug("Tab done, continuing", tab);
    }

    logger.debug("All tabs done.");
    localStorage.removeItem(lockKey);
}
