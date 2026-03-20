export interface InvitationWizardState {
    // Step 1: Flow selection
    flowMode: "existing" | "create";
    selectedFlowSlug?: string;
    selectedFlowPk?: string;
    newFlowName?: string;
    newFlowSlug?: string;
    newStageName?: string;
    continueFlowWithoutInvitation: boolean;

    // Flags for which API calls to make
    needsFlow: boolean;
    needsStage: boolean;
    needsBinding: boolean;

    // Step 2: Invitation details
    invitationName?: string;
    invitationExpires?: string;
    invitationFixedData?: Record<string, unknown>;
    invitationSingleUse: boolean;

    // Results from API calls
    createdStagePk?: string;
    createdFlowPk?: string;
    createdFlowSlug?: string;
    createdInvitationPk?: string;
}
