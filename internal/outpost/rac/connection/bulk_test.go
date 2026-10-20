package connection

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"github.com/wwt/guac"
)

func TestLegacyGuacamoleFileBytesNeverReachControlSocket(t *testing.T) {
	blocked := map[string]struct{}{}
	for _, frame := range []*guac.Instruction{
		guac.NewInstruction("filesystem", "0", "Shared Drive"),
		guac.NewInstruction("file", "7", "application/octet-stream", "report.bin"),
		guac.NewInstruction("blob", "7", "ZmlsZSBieXRlcw=="),
		guac.NewInstruction("ack", "7", "OK", "0"),
		guac.NewInstruction("end", "7"),
	} {
		skip, err := filterLegacyFileInstruction(frame.Byte(), blocked)
		if err != nil || !skip {
			t.Fatalf("file frame reached control socket: %s, %v", frame.Opcode, err)
		}
	}
	if skip, err := filterLegacyFileInstruction(guac.NewInstruction("blob", "8", "clipboard").Byte(), blocked); err != nil || skip {
		t.Fatal("unrelated clipboard stream was blocked")
	}
}

func TestUploadAtomicReplacementAndEmptyFile(t *testing.T) {
	drive := t.TempDir()
	original := filepath.Join(drive, "same.txt")
	if err := os.WriteFile(original, []byte("old"), 0600); err != nil {
		t.Fatal(err)
	}
	root, err := os.OpenRoot(drive)
	if err != nil {
		t.Fatal(err)
	}
	transfer, status := prepareUpload(root, strings.Repeat("a", 36), "/same.txt", 3)
	if status != 200 {
		t.Fatalf("prepare: %d", status)
	}
	if _, err := transfer.file.Write([]byte("new")); err != nil {
		t.Fatal(err)
	}
	transfer.offset = 3
	before, err := os.ReadFile(original)
	if err != nil || string(before) != "old" {
		t.Fatal("destination replaced before finish")
	}
	if transfer.finish() != 200 || !transfer.finished {
		t.Fatal("finish failed")
	}
	transfer.close()
	if !transfer.closed {
		t.Fatal("completed transfer remained open")
	}
	after, err := os.ReadFile(original)
	if err != nil || string(after) != "new" {
		t.Fatal("atomic replacement failed")
	}

	root, err = os.OpenRoot(drive)
	if err != nil {
		t.Fatal(err)
	}
	empty, status := prepareUpload(root, strings.Repeat("b", 36), "/empty", 0)
	if status != 200 || empty.finish() != 200 || !empty.finished {
		t.Fatal("empty upload failed")
	}
	empty.close()
	info, err := os.Stat(filepath.Join(drive, "empty"))
	if err != nil || info.Size() != 0 {
		t.Fatal("empty file missing")
	}
}

func TestControlEnforcesDirectionAndLimit(t *testing.T) {
	connected := make(chan *websocket.Conn, 1)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		socket, err := (&websocket.Upgrader{}).Upgrade(w, r, nil)
		if err != nil {
			t.Error(err)
			return
		}
		connected <- socket
	}))
	defer server.Close()
	client, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = client.Close() }()
	socket := <-connected
	defer func() { _ = socket.Close() }()
	c := &Connection{drivePath: t.TempDir(), ws: socket, writeMu: &sync.Mutex{}, bulk: map[string]*driveTransfer{}}
	request := bulkControlRequest{Request: strings.Repeat("a", 32), Action: "prepare", ID: strings.Repeat("b", 36), Direction: "upload", Path: "/file", Size: 1}
	call := func() int {
		payload, err := json.Marshal(request)
		if err != nil {
			t.Fatal(err)
		}
		if err := c.sendBulkControl(payload); err != nil {
			t.Fatal(err)
		}
		_, frame, err := client.ReadMessage()
		if err != nil {
			t.Fatal(err)
		}
		var reply bulkControlReply
		if err := json.Unmarshal([]byte(strings.TrimPrefix(string(frame), fileBulkPrefix)), &reply); err != nil {
			t.Fatal(err)
		}
		return reply.Status
	}
	if status := call(); status != 403 {
		t.Fatalf("upload permission: %d", status)
	}
	request.Direction = "download"
	if status := call(); status != 403 {
		t.Fatalf("download permission: %d", status)
	}
	c.allowUpload = true
	request.Direction = "upload"
	for index := range 16 {
		c.bulk[formatIndex(index)] = &driveTransfer{}
	}
	if status := call(); status != 429 {
		t.Fatalf("concurrency limit: %d", status)
	}
}

func TestUploadConflictAndCancelCleanup(t *testing.T) {
	drive := t.TempDir()
	if err := os.Mkdir(filepath.Join(drive, "folder"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("folder", filepath.Join(drive, "link")); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"/folder", "/link"} {
		root, err := os.OpenRoot(drive)
		if err != nil {
			t.Fatal(err)
		}
		if transfer, status := prepareUpload(root, strings.Repeat("a", 36), name, 1); status != 409 || transfer != nil {
			t.Fatal("conflict not rejected")
		}
		_ = root.Close()
	}
	root, err := os.OpenRoot(drive)
	if err != nil {
		t.Fatal(err)
	}
	transfer, status := prepareUpload(root, strings.Repeat("a", 36), "/new", 100)
	if status != 200 {
		t.Fatal(status)
	}
	temporary := transfer.temporary
	transfer.close()
	if transfer.finish() != 409 {
		t.Fatal("canceled upload could still finish")
	}
	if _, err := os.Stat(filepath.Join(drive, temporary)); !os.IsNotExist(err) {
		t.Fatal("cancel left temporary file")
	}
}

func TestDownloadHoldsFileAndRejectsSymlink(t *testing.T) {
	drive := t.TempDir()
	file := filepath.Join(drive, "file")
	if err := os.WriteFile(file, []byte("content"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("file", filepath.Join(drive, "link")); err != nil {
		t.Fatal(err)
	}
	root, err := os.OpenRoot(drive)
	if err != nil {
		t.Fatal(err)
	}
	if transfer, status := prepareDownload(root, "x", "/link"); transfer != nil || status != 404 {
		t.Fatal("symlink accepted")
	}
	transfer, status := prepareDownload(root, "x", "/file")
	if status != 200 || transfer.size != 7 {
		t.Fatal("download unavailable")
	}
	if err := os.Rename(file, filepath.Join(drive, "old")); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(file, []byte("replacement"), 0600); err != nil {
		t.Fatal(err)
	}
	content := make([]byte, 7)
	if _, err := transfer.file.Read(content); err != nil || string(content) != "content" {
		t.Fatal("download handle was replaced")
	}
	transfer.close()
}

func bulkSocketPair(t *testing.T) (*websocket.Conn, *websocket.Conn) {
	t.Helper()
	connected := make(chan *websocket.Conn, 1)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		socket, err := (&websocket.Upgrader{}).Upgrade(w, r, nil)
		if err == nil {
			connected <- socket
		}
	}))
	client, _, err := websocket.DefaultDialer.Dial("ws"+strings.TrimPrefix(server.URL, "http"), nil)
	if err != nil {
		server.Close()
		t.Fatal(err)
	}
	socket := <-connected
	t.Cleanup(func() { _ = client.Close(); _ = socket.Close(); server.Close() })
	return socket, client
}

func TestDownloadLengthChangeStopsTransfer(t *testing.T) {
	drive := t.TempDir()
	name := filepath.Join(drive, "changing")
	if err := os.WriteFile(name, make([]byte, 2*bulkFrameSize), 0600); err != nil {
		t.Fatal(err)
	}
	root, err := os.OpenRoot(drive)
	if err != nil {
		t.Fatal(err)
	}
	transfer, status := prepareDownload(root, "id", "/changing")
	if status != 200 {
		t.Fatal(status)
	}
	defer transfer.close()
	socket, client := bulkSocketPair(t)
	result := make(chan bool, 1)
	go func() { result <- (&Connection{}).sendDownload(socket, transfer) }()
	if err := client.WriteJSON(bulkFrame{Type: "start"}); err != nil {
		t.Fatal(err)
	}
	if err := client.WriteJSON(bulkFrame{Type: "credit", Bytes: bulkFrameSize}); err != nil {
		t.Fatal(err)
	}
	if kind, bytes, err := client.ReadMessage(); err != nil || kind != websocket.BinaryMessage || len(bytes) != bulkFrameSize {
		t.Fatalf("first frame: kind=%d bytes=%d err=%v", kind, len(bytes), err)
	}
	if err := os.Truncate(name, 1); err != nil {
		t.Fatal(err)
	}
	if err := client.WriteJSON(bulkFrame{Type: "credit", Bytes: bulkFrameSize}); err != nil {
		t.Fatal(err)
	}
	select {
	case ok := <-result:
		if ok {
			t.Fatal("changed download length reported success")
		}
	case <-time.After(2 * time.Second):
		t.Fatal("download did not stop after length changed")
	}
}

func TestUploadWriteFailureAndConcurrentCancel(t *testing.T) {
	if _, err := os.Stat("/dev/full"); err != nil {
		t.Skip("/dev/full is unavailable")
	}
	full, err := os.OpenFile("/dev/full", os.O_WRONLY, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = full.Close() }()
	transfer := &driveTransfer{direction: "upload", file: full, size: 4}
	socket, client := bulkSocketPair(t)
	done := make(chan struct{})
	go func() { (&Connection{}).receiveUpload(socket, transfer); close(done) }()
	if err := client.WriteJSON(bulkFrame{Type: "start", Offset: 0, Length: 4}); err != nil {
		t.Fatal(err)
	}
	if _, _, err := client.ReadMessage(); err != nil {
		t.Fatal(err)
	}
	if err := client.WriteMessage(websocket.BinaryMessage, []byte("data")); err != nil {
		t.Fatal(err)
	}
	select {
	case <-done:
		if transfer.offset == transfer.size {
			t.Fatal("failed write counted as a completed upload")
		}
	case <-time.After(2 * time.Second):
		t.Fatal("upload did not stop after write failure")
	}

	drive := t.TempDir()
	root, err := os.OpenRoot(drive)
	if err != nil {
		t.Fatal(err)
	}
	concurrent, status := prepareUpload(root, "id", "/cancel", 4)
	if status != 200 {
		t.Fatal(status)
	}
	socket2, client2 := bulkSocketPair(t)
	done2 := make(chan struct{})
	go func() { (&Connection{}).receiveUpload(socket2, concurrent); close(done2) }()
	if err := client2.WriteJSON(bulkFrame{Type: "start", Offset: 0, Length: 4}); err != nil {
		t.Fatal(err)
	}
	if _, _, err := client2.ReadMessage(); err != nil {
		t.Fatal(err)
	}
	closed := make(chan struct{})
	go func() { concurrent.close(); close(closed) }()
	_ = client2.WriteMessage(websocket.BinaryMessage, []byte("data"))
	_ = client2.Close()
	<-closed
	select {
	case <-done2:
	case <-time.After(2 * time.Second):
		t.Fatal("canceled upload kept reading")
	}
}

func TestFinishConcurrentTransferCleanup(t *testing.T) {
	for _, test := range []struct {
		name    string
		cleanup func(*Connection, string)
	}{
		{
			name: "connection_disconnect",
			cleanup: func(c *Connection, _ string) {
				c.cancelAllTransfers()
			},
		},
		{
			name: "transfer_socket_closed",
			cleanup: func(c *Connection, id string) {
				if transfer := c.popTransfer(id); transfer != nil {
					transfer.close()
				}
			},
		},
	} {
		t.Run(test.name, func(t *testing.T) {
			socket, client := bulkSocketPair(t)
			drive := t.TempDir()
			id := "00000000-0000-4000-8000-000000000001"
			request, err := json.Marshal(bulkControlRequest{
				Request: strings.Repeat("a", 32), Action: "finish", ID: id,
			})
			if err != nil {
				t.Fatal(err)
			}
			c := &Connection{ws: socket, writeMu: &sync.Mutex{}}
			// Exercise both orderings of finish and cleanup, including cleanup
			// removing the record after finish has already acquired the transfer.
			for attempt := range 1000 {
				target := filepath.Join(drive, "same.txt")
				if err := os.WriteFile(target, []byte("old"), 0600); err != nil {
					t.Fatal(err)
				}
				root, err := os.OpenRoot(drive)
				if err != nil {
					t.Fatal(err)
				}
				transfer, status := prepareUpload(root, id, "/same.txt", 3)
				if status != 200 {
					_ = root.Close()
					t.Fatalf("prepare: %d", status)
				}
				t.Cleanup(transfer.close)
				if _, err := transfer.file.Write([]byte("new")); err != nil {
					t.Fatal(err)
				}
				transfer.offset = 3
				temporary := filepath.Join(drive, transfer.temporary)
				c.bulk = map[string]*driveTransfer{id: transfer}
				done := make(chan struct{})
				go func() {
					test.cleanup(c, id)
					close(done)
				}()
				err = c.sendBulkControl(request)
				<-done
				if err != nil {
					t.Fatal(err)
				}
				if err := client.SetReadDeadline(time.Now().Add(2 * time.Second)); err != nil {
					t.Fatal(err)
				}
				_, data, err := client.ReadMessage()
				if err != nil {
					t.Fatal(err)
				}
				var reply bulkControlReply
				if err := json.Unmarshal([]byte(strings.TrimPrefix(string(data), fileBulkPrefix)), &reply); err != nil {
					t.Fatal(err)
				}
				if reply.Status != 200 && reply.Status != 404 && reply.Status != 409 {
					t.Fatalf("attempt %d: unexpected finish status %d", attempt, reply.Status)
				}
				if !transfer.closed || transfer.file != nil || transfer.root != nil || len(c.bulk) != 0 {
					t.Fatalf("attempt %d: cleanup left an open transfer", attempt)
				}
				if _, err := os.Stat(temporary); !os.IsNotExist(err) {
					t.Fatalf("attempt %d: temporary file was not removed: %v", attempt, err)
				}
				want := "old"
				if reply.Status == 200 {
					want = "new"
				}
				if content, err := os.ReadFile(target); err != nil || string(content) != want {
					t.Fatalf("attempt %d: target = %q, error = %v; want %q", attempt, content, err, want)
				}
			}
		})
	}
}
