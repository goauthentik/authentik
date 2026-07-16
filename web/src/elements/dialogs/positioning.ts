export const AnchorPositionSupported: boolean =
    CSS.supports("position-anchor", "--x") && CSS.supports("top", "anchor(bottom)");
