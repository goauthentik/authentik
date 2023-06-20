package flow

type StageComponent string

const (
	StageAccessDenied          = StageComponent("ak-stage-access-denied")
	StageAuthenticatorValidate = StageComponent("ak-stage-authenticator-validate")
	StageIdentification        = StageComponent("ak-stage-identification")
	StagePassword              = StageComponent("ak-stage-password")
	StageUserLogin             = StageComponent("ak-stage-user-login")
)

const (
	HeaderAuthentikRemoteIP     = "X-authentik-remote-ip"
	HeaderAuthentikOutpostToken = "X-authentik-outpost-token"
)
