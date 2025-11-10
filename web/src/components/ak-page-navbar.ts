import { AKPageNavbar } from "./ak-page-navbar-impl/ak-page-navbar.component";
import {
    PageDetailsUpdate,
    PageNavMenuToggle,
    setPageDetails,
} from "./ak-page-navbar-impl/ak-page-navbar.events";

export { AKPageNavbar, PageDetailsUpdate, PageNavMenuToggle, setPageDetails };

window.customElements.define("ak-page-navbar", AKPageNavbar);
