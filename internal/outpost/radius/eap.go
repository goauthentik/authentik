package radius

// https://datatracker.ietf.org/doc/html/rfc3748#section-6.1

const (
	EAPMessageCodeRequest  byte = 1
	EAPMessageCodeResponse byte = 2
	EAPMessageCodeSuccess  byte = 3
	EAPMessageCodeFailure  byte = 4
)

const (
	EAPMessageTypeIdentity         byte = 1
	EAPMessageTypeNotification     byte = 2
	EAPMessageTypeNakResponse      byte = 3
	EAPMessageTypeMD5Challenge     byte = 4
	EAPMessageTypeOneTimePassword  byte = 5
	EAPMessageTypeGenericTokenCard byte = 6
	EAPMessageTypeExpandedNak      byte = 254
)
