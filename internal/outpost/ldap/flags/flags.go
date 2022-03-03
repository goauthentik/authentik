package flags

import "goauthentik.io/api/v3"

type UserFlags struct {
	UserInfo  *api.User
	UserPk    int32
	CanSearch bool
}
