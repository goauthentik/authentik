import { customElement } from "lit/decorators.js";

import type { Flow } from "@goauthentik/api";

import FlowSearch from "./FlowSearch";

@customElement("ak-flow-search")
export class AkFlowSearch<T extends Flow> extends FlowSearch<T> {}

export default AkFlowSearch;
