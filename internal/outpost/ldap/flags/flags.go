package flags

import "goauthentik.io/api"

type UserFlags struct {
	UserInfo  *api.User
	UserPk    int32
	CanSearch bool
}
