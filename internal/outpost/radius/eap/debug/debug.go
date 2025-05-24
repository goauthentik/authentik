package debug

import (
	"fmt"
)

func FormatBytes(d []byte) string {
	b := d
	if len(b) > 32 {
		b = b[:32]
	}
	return fmt.Sprintf("% x", b)
}
