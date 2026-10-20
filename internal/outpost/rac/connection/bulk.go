package connection

import (
	"context"
	"crypto/rand"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"goauthentik.io/internal/config"
	"goauthentik.io/internal/constants"
)

const fileBulkPrefix = "0.authentik.bulk."
const bulkFrameSize = 256 * 1024
const bulkWindow = 512 * 1024

type bulkControlRequest struct {
	Request   string `json:"request"`
	Action    string `json:"action"`
	ID        string `json:"id"`
	Path      string `json:"path"`
	Direction string `json:"direction"`
	Size      int64  `json:"size"`
	Tenant    string `json:"tenant"`
}

type bulkControlReply struct {
	Request string `json:"request"`
	ID      string `json:"id,omitempty"`
	Status  int    `json:"status"`
	Size    int64  `json:"size"`
}

type bulkFrame struct {
	Type   string `json:"type"`
	Offset int64  `json:"offset,omitempty"`
	Length int64  `json:"length,omitempty"`
	Bytes  int64  `json:"bytes,omitempty"`
}

type driveTransfer struct {
	id           string
	direction    string
	root         *os.Root
	file         *os.File
	temporary    string
	target       string
	size         int64
	offset       int64
	mu           sync.Mutex
	cancel       context.CancelFunc
	lastActivity time.Time
	tenant       string
	finished     bool
	closed       bool
}

func randomTemporaryName() (string, error) {
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return "", err
	}
	return ".authentik-upload-" + hex.EncodeToString(nonce[:]), nil
}

// Open a download once. The file descriptor remains pinned if the name is
// replaced while the transfer is in progress.
func prepareDownload(root *os.Root, id, virtual string) (*driveTransfer, int) {
	relative := strings.TrimPrefix(virtual, "/")
	before, err := root.Lstat(relative)
	if err != nil || !before.Mode().IsRegular() {
		return nil, 404
	}
	file, err := root.Open(relative)
	if err != nil {
		return nil, 503
	}
	after, err := file.Stat()
	if err != nil || !after.Mode().IsRegular() || !os.SameFile(before, after) {
		_ = file.Close()
		return nil, 409
	}
	return &driveTransfer{id: id, direction: "download", root: root, file: file, size: after.Size(), lastActivity: time.Now()}, 200
}

// Write uploads beside their target so that finish can replace an ordinary
// file with one atomic rename. A symlink or directory at the target conflicts.
func prepareUpload(root *os.Root, id, virtual string, size int64) (*driveTransfer, int) {
	relative := strings.TrimPrefix(virtual, "/")
	parent := path.Dir(relative)
	info, err := root.Stat(parent)
	if err != nil || !info.IsDir() {
		return nil, 404
	}
	if target, err := root.Lstat(relative); err == nil && !target.Mode().IsRegular() {
		return nil, 409
	} else if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, 503
	}
	name, err := randomTemporaryName()
	if err != nil {
		return nil, 503
	}
	temporary := path.Join(parent, name)
	file, err := root.OpenFile(temporary, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return nil, 503
	}
	return &driveTransfer{id: id, direction: "upload", root: root, file: file, target: relative, temporary: temporary, size: size, lastActivity: time.Now()}, 200
}

func (transfer *driveTransfer) finish() int {
	transfer.mu.Lock()
	defer transfer.mu.Unlock()
	if transfer.closed || transfer.file == nil || transfer.direction != "upload" || transfer.offset != transfer.size {
		return 409
	}
	if err := transfer.file.Sync(); err != nil {
		return 503
	}
	if err := transfer.file.Close(); err != nil {
		return 503
	}
	transfer.file = nil
	if target, err := transfer.root.Lstat(transfer.target); err == nil && !target.Mode().IsRegular() {
		return 409
	} else if err != nil && !errors.Is(err, os.ErrNotExist) {
		return 503
	}
	if err := transfer.root.Rename(transfer.temporary, transfer.target); err != nil {
		return 503
	}
	transfer.temporary = ""
	transfer.finished = true
	return 200
}

func (transfer *driveTransfer) close() {
	transfer.mu.Lock()
	defer transfer.mu.Unlock()
	transfer.closed = true
	if transfer.cancel != nil {
		transfer.cancel()
	}
	if transfer.file != nil {
		_ = transfer.file.Close()
		transfer.file = nil
	}
	if transfer.root != nil {
		if transfer.temporary != "" {
			_ = transfer.root.Remove(transfer.temporary)
		}
		_ = transfer.root.Close()
		transfer.root = nil
	}
}

func (c *Connection) popTransfer(id string) *driveTransfer {
	c.bulkMu.Lock()
	defer c.bulkMu.Unlock()
	transfer := c.bulk[id]
	delete(c.bulk, id)
	return transfer
}

func (c *Connection) cancelAllTransfers() {
	c.bulkMu.Lock()
	transfers := c.bulk
	c.bulk = make(map[string]*driveTransfer)
	c.bulkMu.Unlock()
	for _, transfer := range transfers {
		transfer.close()
	}
}

func (c *Connection) sendBulkControl(data []byte) error {
	var request bulkControlRequest
	if len(data) > 8192 || json.Unmarshal(data, &request) != nil {
		return nil
	}
	reply := bulkControlReply{Request: request.Request, Status: 400}
	if len(request.Request) != 32 || len(request.ID) != 36 {
		return nil
	}
	switch request.Action {
	case "prepare":
		if !validVirtualPath(request.Path) || request.Path == "/" || request.Size < 0 ||
			c.drivePath == "" || request.Direction != "upload" && request.Direction != "download" {
			break
		}
		if request.Direction == "upload" && !c.allowUpload || request.Direction == "download" && !c.allowDownload {
			reply.Status = 403
			break
		}
		c.bulkMu.Lock()
		if len(c.bulk) >= 16 || c.bulk[request.ID] != nil {
			c.bulkMu.Unlock()
			reply.Status = 429
			break
		}
		root, err := os.OpenRoot(c.drivePath)
		if err != nil {
			c.bulkMu.Unlock()
			reply.Status = 503
			break
		}
		var transfer *driveTransfer
		if request.Direction == "download" {
			transfer, reply.Status = prepareDownload(root, request.ID, request.Path)
		} else {
			transfer, reply.Status = prepareUpload(root, request.ID, request.Path, request.Size)
		}
		if transfer == nil {
			_ = root.Close()
		} else {
			transfer.tenant = request.Tenant
			c.bulk[request.ID] = transfer
			reply.Size = transfer.size
		}
		c.bulkMu.Unlock()
		if transfer != nil {
			go c.serveTransfer(transfer)
		}
	case "finish":
		c.bulkMu.Lock()
		transfer := c.bulk[request.ID]
		c.bulkMu.Unlock()
		if transfer == nil {
			reply.Status = 404
		} else {
			reply.Status = transfer.finish()
			if reply.Status == 200 {
				// Connection or socket cleanup may already have removed the transfer.
				if removed := c.popTransfer(request.ID); removed != nil {
					removed.close()
				}
			}
		}
	case "cancel":
		if transfer := c.popTransfer(request.ID); transfer != nil {
			transfer.close()
		}
		reply.Status = 200
	}
	encoded, err := json.Marshal(reply)
	if err != nil {
		return err
	}
	return c.writeSocket(append([]byte(fileBulkPrefix), encoded...))
}

func (c *Connection) bulkURL(id string) string {
	scheme := strings.ReplaceAll(c.ac.Client.GetConfig().Scheme, "http", "ws")
	return fmt.Sprintf("%s://%s/ws/rac/bulk/%s/", scheme, c.ac.Client.GetConfig().Host, id)
}

func (c *Connection) serveTransfer(transfer *driveTransfer) {
	terminalStatus := 503
	defer func() {
		transfer.mu.Lock()
		if transfer.finished {
			terminalStatus = 200
		}
		transfer.mu.Unlock()
		terminal, err := json.Marshal(bulkControlReply{ID: transfer.id, Status: terminalStatus})
		if err == nil {
			_ = c.writeSocket(append([]byte(fileBulkPrefix), terminal...))
		}
	}()
	header := http.Header{
		"Authorization": []string{"Bearer " + c.ac.Token()},
		"User-Agent":    []string{constants.UserAgentOutpost()},
		"X-RAC-Tenant":  []string{transfer.tenant},
	}
	dialer := websocket.Dialer{Proxy: http.ProxyFromEnvironment, HandshakeTimeout: 10 * time.Second,
		TLSClientConfig: &tls.Config{InsecureSkipVerify: config.Get().AuthentikInsecure}}
	var ws *websocket.Conn
	var err error
	for attempt := 0; attempt < 20; attempt++ {
		transfer.mu.Lock()
		closed := transfer.closed
		transfer.mu.Unlock()
		if closed {
			return
		}
		ws, _, err = dialer.Dial(c.bulkURL(transfer.id), header)
		if err == nil || c.ctx.Err() != nil {
			break
		}
		time.Sleep(250 * time.Millisecond)
	}
	if err != nil {
		if removed := c.popTransfer(transfer.id); removed != nil {
			removed.close()
		}
		return
	}
	defer func() {
		_ = ws.Close()
		if removed := c.popTransfer(transfer.id); removed != nil {
			removed.close()
		}
	}()
	ctx, cancel := context.WithCancel(c.ctx)
	transfer.mu.Lock()
	if transfer.closed {
		transfer.mu.Unlock()
		cancel()
		return
	}
	transfer.cancel = cancel
	transfer.mu.Unlock()
	go func() { <-ctx.Done(); _ = ws.Close() }()
	if transfer.direction == "upload" {
		c.receiveUpload(ws, transfer)
	} else {
		if c.sendDownload(ws, transfer) {
			terminalStatus = 200
		}
	}
}

func writeBulkFrame(ws *websocket.Conn, frame bulkFrame) error {
	_ = ws.SetWriteDeadline(time.Now().Add(60 * time.Second))
	return ws.WriteJSON(frame)
}

func (c *Connection) receiveUpload(ws *websocket.Conn, transfer *driveTransfer) {
	var remaining int64
	var availableCredit int64
	var pendingCredit int64
	ws.SetReadLimit(bulkFrameSize)
	for {
		_ = ws.SetReadDeadline(time.Now().Add(60 * time.Second))
		kind, data, err := ws.ReadMessage()
		if err != nil {
			return
		}
		if kind == websocket.TextMessage {
			var frame bulkFrame
			if json.Unmarshal(data, &frame) != nil || frame.Type != "start" || remaining != 0 ||
				frame.Offset != transfer.offset || frame.Length <= 0 || frame.Length > 4*1024*1024 ||
				frame.Length > transfer.size-frame.Offset {
				return
			}
			remaining = frame.Length
			availableCredit = bulkWindow
			pendingCredit = 0
			if writeBulkFrame(ws, bulkFrame{Type: "credit", Bytes: bulkWindow, Offset: transfer.offset}) != nil {
				return
			}
			continue
		}
		if kind != websocket.BinaryMessage || remaining == 0 || len(data) == 0 || len(data) > bulkFrameSize ||
			int64(len(data)) > remaining || int64(len(data)) > availableCredit {
			return
		}
		transfer.mu.Lock()
		if transfer.closed || transfer.file == nil {
			transfer.mu.Unlock()
			return
		}
		written, err := transfer.file.Write(data)
		transfer.offset += int64(written)
		transfer.lastActivity = time.Now()
		offset := transfer.offset
		transfer.mu.Unlock()
		if err != nil || written != len(data) {
			return
		}
		remaining -= int64(written)
		availableCredit -= int64(written)
		pendingCredit += int64(written)
		if pendingCredit >= bulkWindow/2 || remaining == 0 {
			if writeBulkFrame(ws, bulkFrame{Type: "credit", Bytes: pendingCredit, Offset: offset}) != nil {
				return
			}
			availableCredit += pendingCredit
			pendingCredit = 0
		}
	}
}

func (c *Connection) sendDownload(ws *websocket.Conn, transfer *driveTransfer) bool {
	transfer.mu.Lock()
	file := transfer.file
	closed := transfer.closed
	transfer.mu.Unlock()
	if closed || file == nil {
		return false
	}
	_ = ws.SetReadDeadline(time.Now().Add(60 * time.Second))
	_, data, err := ws.ReadMessage()
	var frame bulkFrame
	if err != nil || json.Unmarshal(data, &frame) != nil || frame.Type != "start" {
		return false
	}
	credit := int64(0)
	buffer := make([]byte, bulkFrameSize)
	for transfer.offset < transfer.size {
		if credit == 0 {
			_ = ws.SetReadDeadline(time.Now().Add(60 * time.Second))
			kind, data, err := ws.ReadMessage()
			if err != nil || kind != websocket.TextMessage || json.Unmarshal(data, &frame) != nil || frame.Type != "credit" || frame.Bytes <= 0 || frame.Bytes > bulkWindow {
				return false
			}
			credit += frame.Bytes
		}
		limit := min(int64(len(buffer)), credit, transfer.size-transfer.offset)
		info, err := file.Stat()
		if err != nil || info.Size() != transfer.size {
			return false
		}
		count, err := io.ReadFull(file, buffer[:int(limit)])
		if err != nil || count != int(limit) {
			return false
		}
		_ = ws.SetWriteDeadline(time.Now().Add(60 * time.Second))
		if err := ws.WriteMessage(websocket.BinaryMessage, buffer[:count]); err != nil {
			return false
		}
		transfer.offset += int64(count)
		credit -= int64(count)
		transfer.lastActivity = time.Now()
	}
	info, err := file.Stat()
	if err != nil || info.Size() != transfer.size {
		return false
	}
	var extra [1]byte
	if n, err := file.Read(extra[:]); n != 0 || err != io.EOF {
		return false
	}
	return writeBulkFrame(ws, bulkFrame{Type: "complete", Offset: transfer.offset}) == nil
}
