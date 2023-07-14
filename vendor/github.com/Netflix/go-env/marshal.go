package env

// Marshaler is the interface implemented by types that can marshal themselves into valid environment variable values.
type Marshaler interface {
	MarshalEnvironmentValue() (string, error)
}
