import { createContext } from "@lit-labs/context";

import { WizardStep } from "./types";

export const akWizardStepsContextName = createContext<WizardStep[]>(Symbol("ak-wizard-steps"));

export default akWizardStepsContextName;
