package tls

type Flag byte

const (
	FlagLengthIncluded Flag = 1 << 7
	FlagMoreFragments  Flag = 1 << 6
	FlagTLSStart       Flag = 1 << 5
	FlagNone           Flag = 0
)
