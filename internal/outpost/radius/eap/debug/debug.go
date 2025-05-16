package debug

import (
	"fmt"

	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	log "github.com/sirupsen/logrus"
	"layeh.com/radius"
)

func DebugPacket(p *radius.Packet) {
	log.Debug(p)
	log.Debug(p.Attributes)
	n, _ := p.Encode()
	log.Debug(n)
	packet := gopacket.NewPacket(n, layers.LayerTypeRADIUS, gopacket.Default)
	layer := packet.Layer(layers.LayerTypeRADIUS)
	if layer == nil {
		return
	}
	log.Debug(layer.(*layers.RADIUS))
}

func FormatBytes(d []byte) string {
	b := d
	if len(b) > 32 {
		b = b[:32]
	}
	return fmt.Sprintf("% x", b)
}
