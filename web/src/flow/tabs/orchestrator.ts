import { globalAK } from "#common/global";

import { Broadcast } from "#flow/tabs/broadcast";
import { TabID } from "#flow/tabs/TabID";

import { ConsoleLogger } from "#logger/browser";

const lockKey = "authentik-tab-locked";
const logger = ConsoleLogger.prefix("mtab/orchestrate");

const TAB_EXIT_TIMEOUT_MS = 3000;

export function multiTabOrchestrateLeave() {
    Broadcast.shared.akExitTab();
    TabID.shared.clear();
}

export async function multiTabOrchestrateResume() {
    if (!globalAK().brand.flags.flowsContinuousLogin) {
        return;
    }

    const lockTabID = localStorage.getItem(lockKey);
    const tabs = await Broadcast.shared.akTabDiscover();

    logger.debug("Got list of tabs", tabs);

    if (lockTabID && tabs.has(lockTabID)) {
        logger.debug("Tabs locked, leaving.");
        multiTabOrchestrateLeave();
        return;
    }

    logger.debug("Locking tabs");
    localStorage.setItem(lockKey, TabID.shared.current);

    for (const tab of tabs) {
        logger.debug("Telling tab to continue", tab);
        Broadcast.shared.akResumeTab(tab);

        const done = Promise.withResolvers<void>();

        let timeout = -1;

        const checker = requestAnimationFrame(() => {
            if (Broadcast.shared.exitedTabIDs.includes(tab)) {
                logger.debug("tab exited", tab);
                self.clearTimeout(timeout);

                self.setTimeout(() => {
                    logger.debug("continue exited", tab);
                    done.resolve();
                }, 1000);

                cancelAnimationFrame(checker);
            }
        });

        timeout = self.setTimeout(() => {
            logger.warn("Timed out waiting for tab to exit, moving on", tab);
            cancelAnimationFrame(checker);
            done.resolve();
        }, TAB_EXIT_TIMEOUT_MS);

        await done.promise;

        logger.debug("Tab done, continuing", tab);
    }

    logger.debug("All tabs done.");
    localStorage.removeItem(lockKey);
}
