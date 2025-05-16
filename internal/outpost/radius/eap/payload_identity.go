package eap

type IdentityPayload struct {
	Identity string
}

func (ip *IdentityPayload) Decode(raw []byte) error {
	ip.Identity = string(raw)
	return nil
}

func (ip *IdentityPayload) Encode() ([]byte, error) {
	return []byte{}, nil
}
