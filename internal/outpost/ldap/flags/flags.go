package flags

import (
	"crypto/sha256"
	"encoding/hex"
	"net/http"

	"goauthentik.io/api/v3"
)

const InvalidUserPK = -1

type UserFlags struct {
	UserInfo  *api.User
	UserPk    int32
	CanSearch bool
	Session   *http.Cookie
}

func (uf UserFlags) SessionID() string {
	if uf.Session == nil {
		return ""
	}
	h := sha256.New()
	h.Write([]byte(uf.Session.Value))
	return hex.EncodeToString(h.Sum(nil))
}
