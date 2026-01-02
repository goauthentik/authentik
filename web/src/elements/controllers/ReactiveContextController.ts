import { EVENT_REFRESH } from "#common/constants";
import { isCausedByAbortError, parseAPIResponseError } from "#common/errors/network";
import { createDebugLogger } from "#common/logger";

import {
    ReactiveContextController as IReactiveContextController,
    ReactiveElementHost,
} from "#elements/types";

import { Context, ContextProvider } from "@lit/context";

/**
 * A base Lit controller for API-backed context providers.
 *
 * Subclasses must implement {@linkcode apiEndpoint} and {@linkcode doRefresh}
 * to fetch data and update the context value, respectively.
 */
export abstract class ReactiveContextController<
    Value extends object,
    Host extends object = object,
> implements IReactiveContextController<Context<symbol, Value>, Host> {
    public abstract context: ContextProvider<Context<symbol, Value>>;
    public abstract host: ReactiveElementHost<Host>;

    /**
     * A prefix for log messages from this controller.
     */
    protected static logPrefix = "controller";
    /**
     * An event name that triggers a refresh when dispatched on the global context.
     */
    protected static refreshEvent = EVENT_REFRESH;

    /**
     * Log a debug message with the controller's prefix.
     *
     * @todo Port `ConsoleLogger` here for better logging.
     */
    protected debug: (...args: unknown[]) => void;

    /**
     * An {@linkcode AbortController} that can be used to cancel ongoing refreshes.
     *
     * Generally this is handled automatically by {@linkcode refresh},
     * but may be useful for subclasses with unique behavior.
     */
    protected abortController: null | AbortController = null;

    /**
     * An {@linkcode AbortController} that can be used to cancel ongoing operations
     * when the host disconnects.
     */
    protected hostAbortController: AbortController | null = null;

    public constructor() {
        const { logPrefix } = this.constructor as typeof ReactiveContextController;

        this.debug = createDebugLogger("context", logPrefix);
    }

    /**
     * Updates the context value with the provided data.
     *
     * @param data The data to set in the context.
     *
     * @see {@linkcode refresh} for fetching new data.
     */
    protected abstract doRefresh(data: Value): void | Promise<void>;

    /**
     * Fetches data from the API endpoint.
     *
     * @param requestInit Optional request initialization parameters.
     * @returns A promise that resolves to the fetched data.
     */
    protected abstract apiEndpoint(requestInit?: RequestInit): Promise<Value>;

    /**
     * Refreshes the context by calling the API endpoint and updating the context value.
     *
     * @see {@linkcode apiEndpoint} for the API call.
     * @see {@linkcode doRefresh} for updating the context value.
     */
    public refresh = (): Promise<Value | null> => {
        this.abort("Refresh aborted by new refresh call");

        this.debug("Refresh requested...");

        this.abortController?.abort();

        this.abortController = new AbortController();

        return this.apiEndpoint({
            signal: this.abortController.signal,
        })
            .then(async (data) => {
                await this.doRefresh(data);

                return data;
            })
            .catch(this.suppressAbortError)
            .catch(this.reportRefreshError);
    };

    /**
     * A helper function to gracefully handle aborted requests.
     *
     * @see {@linkcode isCausedByAbortError} for the underlying implementation.
     */
    protected suppressAbortError = (error: unknown) => {
        if (isCausedByAbortError(error)) {
            this.debug("Aborted:", error.message);

            return null;
        }

        throw error;
    };

    /**
     * Reports an error that occurred during session refresh.
     *
     * @param error The error to report.
     */
    protected reportRefreshError = async (error: unknown) => {
        const parsedError = await parseAPIResponseError(error);

        this.debug(parsedError);

        return null;
    };

    /**
     * Abort the ongoing request, if any.
     *
     * @param message An optional message for the abort reason.
     */
    protected abort(message?: string): void {
        // Do we have a controller to abort?
        if (!this.abortController) return;

        const Constructor = this.constructor as typeof ReactiveContextController;
        const logPrefix = Constructor.logPrefix;

        const reason = new DOMException(`${logPrefix}: ${message ?? "Aborted"}`, "AbortError");

        this.abortController.abort(reason);
        this.abortController = null;
    }

    /**
     * Registers the refresh event on the window.
     *
     * This is called automatically when the host connects.
     *
     * @see {@linkcode hostConnected} for more details.
     */
    protected registerRefreshEvent() {
        this.hostAbortController = new AbortController();

        const Constructor = this.constructor as typeof ReactiveContextController;

        window.addEventListener(Constructor.refreshEvent, this.refresh, {
            signal: this.hostAbortController.signal,
        });
    }

    /**
     * Called when the host is connected.
     *
     * This method may be overridden without calling `super.hostConnected()`.
     *
     * @see {@linkcode registerRefreshEvent} to manually register the refresh event.
     */
    public hostConnected() {
        this.registerRefreshEvent();
    }

    /**
     * Called when the host is disconnected.
     *
     * If this method is overridden, be sure to call `super.hostDisconnected()`
     * to abort ongoing network requests.
     */
    public hostDisconnected() {
        const Constructor = this.constructor as typeof ReactiveContextController;
        const logPrefix = Constructor.logPrefix;

        const reason = new DOMException(`${logPrefix}: Host disconnected`, "AbortError");

        this.hostAbortController?.abort(reason);
        this.abortController?.abort(reason);

        this.hostAbortController = null;
        this.abortController = null;
    }
}
