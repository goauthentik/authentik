import { type AkDrawer } from "./ak-drawer.component";

import { match, P } from "ts-pattern";

import { ReactiveController, ReactiveControllerHost } from "lit";

type DrawerResizeControllerHost = ReactiveControllerHost & AkDrawer;
type Position = "start" | "end" | "left" | "right" | "bottom";

const oneOf = P.union;

const DEFAULT_SIZE_PROPERTY_NAME = "--ak-v2-c-drawer__panel--md--FlexBasis";
const DEFAULT_RESIZE_INCREMENT = 5;

interface ResizeControllerProps {
    sizeProperty?: string;
    resizeIncrement?: number;
}

export class DrawerResizeController implements ReactiveController {
    #abortController: AbortController | null = null;

    #positions: {
        start: number;
        end: number;
        bottom: number;
    } = { start: 0, end: 0, bottom: 0 };

    public resizeIncrement: number;
    public sizeProperty: string;

    constructor(
        private host: DrawerResizeControllerHost,
        props: ResizeControllerProps = {},
    ) {
        this.resizeIncrement = props.resizeIncrement ?? DEFAULT_RESIZE_INCREMENT;
        this.sizeProperty = props.sizeProperty ?? DEFAULT_SIZE_PROPERTY_NAME;
    }

    endController() {
        this.#abortController?.abort();
        this.#abortController = null;
    }

    restartController() {
        this.endController();
        this.#abortController = new AbortController();
        return this.#abortController.signal;
    }

    hostQ(part: string): HTMLElement {
        const element = this.host.renderRoot.querySelector(part);
        if (element === null || !(element instanceof HTMLElement)) {
            throw new Error(`Could not identify requested part ${element}`);
        }
        return element;
    }

    get drawer() {
        return this.hostQ('[part="drawer"]');
    }

    get panel() {
        return this.hostQ('[part="drawer-panel"]');
    }

    get content() {
        return this.hostQ('[part="drawer-panel-main"]');
    }

    get splitter() {
        return this.hostQ('[part="drawer-splitter"]');
    }

    get inline() {
        return this.host.hasAttribute("inline");
    }

    get position(): Position {
        return (this.host.getAttribute("position") || "end") as Position;
    }

    initPositions() {
        const pan = this.panel.getBoundingClientRect();
        this.#positions = { start: pan.left, end: pan.right, bottom: pan.bottom };
    }

    setResizing(resizing: boolean = true) {
        if (resizing) {
            this.host.setAttribute("resizing", "");
        } else {
            this.host.removeAttribute("resizing");
        }
    }

    get isResizing() {
        return this.host.hasAttribute("resizing");
    }

    handleMove(ev: MouseEvent | TouchEvent, controlPosition: number) {
        ev.stopPropagation();
        const newSize = match(this.position)
            .with(oneOf("end", "right"), () => this.#positions.end - controlPosition)
            .with(oneOf("start", "left"), () => controlPosition - this.#positions.start)
            .with("bottom", () => this.#positions.bottom - controlPosition)
            .otherwise(() => {
                throw new Error(`Do not recognize position: ${this.position}`);
            });
        if (this.position === "bottom") {
            this.panel.style.overflowAnchor = "none";
        }
        this.panel.style.setProperty(DEFAULT_SIZE_PROPERTY_NAME, `${newSize}px`);
    }

    handleMouseMove = (ev: MouseEvent) => {
        this.handleMove(ev, this.position === "bottom" ? ev.clientY : ev.clientX);
    };

    handleTouchMove = (ev: TouchEvent) => {
        ev.preventDefault();
        ev.stopImmediatePropagation();
        const touch = ev.touches[0];
        this.handleMove(ev, this.position === "bottom" ? touch.clientY : touch.clientX);
    };

    handleMouseUp = () => {
        this.setResizing(false);
        this.initPositions();
        this.restartController();
    };

    handleTouchEnd = (ev: TouchEvent) => {
        ev.stopPropagation();
        this.handleMouseUp();
    };

    handleTouchStart = (ev: TouchEvent) => {
        ev.stopPropagation();
        const signal = this.restartController();
        document.addEventListener("touchmove", this.handleTouchMove, { passive: false, signal });
        document.addEventListener("touchend", this.handleTouchEnd, { signal });
        this.initPositions();
        this.setResizing();
    };

    handleMouseDown = (ev: MouseEvent) => {
        ev.stopPropagation();
        ev.preventDefault();
        const signal = this.restartController();
        document.addEventListener("mousemove", this.handleMouseMove, { signal });
        document.addEventListener("mouseup", this.handleMouseUp, { signal });
        this.initPositions();
        this.setResizing();
    };

    handleKeyDown = (ev: KeyboardEvent) => {
        const key = ev.key;
        const positionKeys =
            this.position === "bottom" ? ["ArrowUp", "ArrowDown"] : ["ArrowLeft", "ArrowRight"];
        const validKeys = ["Escape", "Enter", ...positionKeys];

        // Prevent default behavior when resizing, but otherwise let it pass.
        if (!validKeys.includes(key)) {
            if (this.isResizing) {
                ev.preventDefault();
            }
            return;
        }
        ev.preventDefault();

        const delta = match([key, this.position])
            .with(["ArrowRight", oneOf("end", "right")], () => -1 * this.resizeIncrement)
            .with(["ArrowLeft", oneOf("end", "right")], () => this.resizeIncrement)
            .with(["ArrowRight", oneOf("start", "left")], () => this.resizeIncrement)
            .with(["ArrowLeft", oneOf("start", "left")], () => -1 * this.resizeIncrement)
            .with(["ArrowUp", "bottom"], () => this.resizeIncrement)
            .with(["ArrowDown", "bottom"], () => -1 * this.resizeIncrement)
            .otherwise(() => 0);

        const { height, width } = this.panel.getBoundingClientRect();
        const newSize = (this.position === "bottom" ? height : width) + delta;
        this.panel.style.setProperty(DEFAULT_SIZE_PROPERTY_NAME, `${newSize}px`);
    };

    hostConnected() {
        this.host.updateComplete.then(() => {
            this.initPositions();
        });
    }

    hostDisconnected() {
        this.#abortController?.abort();
        this.#abortController = null;
    }
}
