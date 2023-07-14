package env

// Unmarshaler is the interface implemented by types that can unmarshal an
// environment variable value representation of themselves. The input can be
// assumed to be the raw string value stored in the environment.
type Unmarshaler interface {
	UnmarshalEnvironmentValue(data string) error
}
