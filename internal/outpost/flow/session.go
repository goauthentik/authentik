package flow

import "github.com/golang-jwt/jwt/v5"

type SessionCookieClaims struct {
	jwt.Claims

	SessionID     string `json:"sid"`
	Authenticated bool   `json:"authenticated"`
}

func (fe *FlowExecutor) Session() *jwt.Token {
	sc := fe.SessionCookie()
	if sc == nil {
		return nil
	}
	t, _, _ := jwt.NewParser().ParseUnverified(sc.Value, &SessionCookieClaims{})
	// During testing the session cookie value is not a JWT but rather just the session ID
	// in which case we wrap that in a pseudo-JWT
	if t == nil {
		return &jwt.Token{
			Claims: &SessionCookieClaims{
				SessionID: sc.Value,
			},
		}
	}
	return t
}
