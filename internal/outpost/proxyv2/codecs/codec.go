package codecs

import (
	"math"

	"github.com/gorilla/securecookie"
	log "github.com/sirupsen/logrus"
)

type Codec struct {
	*securecookie.SecureCookie
}

func New(maxAge int, hashKey, blockKey []byte) *Codec {
	cookie := securecookie.New(hashKey, blockKey)
	cookie.MaxAge(maxAge)
	cookie.MaxLength(math.MaxInt)
	return &Codec{
		SecureCookie: cookie,
	}
}

func CodecsFromPairs(maxAge int, keyPairs ...[]byte) []securecookie.Codec {
	codecs := make([]securecookie.Codec, len(keyPairs)/2+len(keyPairs)%2)
	for i := 0; i < len(keyPairs); i += 2 {
		var blockKey []byte
		if i+1 < len(keyPairs) {
			blockKey = keyPairs[i+1]
		}
		codecs[i/2] = New(maxAge, keyPairs[i], blockKey)
	}
	return codecs
}

func (s *Codec) Encode(name string, value interface{}) (string, error) {
	log.Trace("cookie encode")
	return s.SecureCookie.Encode("authentik_proxy", value)
}

func (s *Codec) Decode(name string, value string, dst interface{}) error {
	log.Trace("cookie decode")
	return s.SecureCookie.Decode("authentik_proxy", value, dst)
}
