package flow

type StageComponent string

const (
	StageIdentification        = StageComponent("ak-stage-identification")
	StagePassword              = StageComponent("ak-stage-password")
	StageAuthenticatorValidate = StageComponent("ak-stage-authenticator-validate")
	StageAccessDenied          = StageComponent("ak-stage-access-denied")
)

const (
	HeaderAuthentikRemoteIP     = "X-authentik-remote-ip"
	HeaderAuthentikOutpostToken = "X-authentik-outpost-token"
)

const CodePasswordSeparator = ";"
