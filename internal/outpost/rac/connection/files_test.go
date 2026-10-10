package connection

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDirectoryPaginationAndKinds(t *testing.T) {
	drive := t.TempDir()
	for index := range 205 {
		name := filepath.Join(drive, "item-"+formatIndex(index))
		if err := os.WriteFile(name, []byte{1, 2, 3}, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.Mkdir(filepath.Join(drive, "folder"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("item-000", filepath.Join(drive, "link")); err != nil {
		t.Fatal(err)
	}
	first := listDirectory(drive, directoryRequest{Request: strings.Repeat("a", 32), Path: "/"})
	if first.Status != 200 || len(first.Entries) != 200 || first.Cursor == "" {
		t.Fatalf("first page: %+v", first)
	}
	second := listDirectory(drive, directoryRequest{Request: strings.Repeat("b", 32), Path: "/", Cursor: first.Cursor})
	if second.Status != 200 || len(second.Entries) != 6 || second.Cursor != "" {
		t.Fatalf("second page: %+v", second)
	}
	if first.Entries[0].Name != "folder" || first.Entries[0].Kind != "directory" {
		t.Fatal("directory entry missing")
	}
	for _, entry := range append(first.Entries, second.Entries...) {
		if entry.Name == "link" {
			t.Fatal("symlink shown")
		}
		if entry.Kind == "file" && (entry.Size == nil || *entry.Size != 3) {
			t.Fatal("file size missing")
		}
	}
}

func TestDirectoryReplyStaysWithinControlMessageLimit(t *testing.T) {
	drive := t.TempDir()
	virtual := ""
	actual := drive
	for range 30 {
		part := strings.Repeat("a", 120)
		virtual += "/" + part
		actual = filepath.Join(actual, part)
		if err := os.Mkdir(actual, 0700); err != nil {
			t.Fatal(err)
		}
	}
	for index := range 80 {
		if err := os.WriteFile(filepath.Join(actual, "item-"+formatIndex(index)), nil, 0600); err != nil {
			t.Fatal(err)
		}
	}
	cursor := ""
	total := 0
	for {
		page := listDirectory(drive, directoryRequest{Request: strings.Repeat("a", 32), Path: virtual, Cursor: cursor})
		encoded, err := json.Marshal(page)
		if err != nil || page.Status != 200 || len(encoded)+len(fileListPrefix) > maxDirectoryReply {
			t.Fatalf("oversized control page: status=%d bytes=%d err=%v", page.Status, len(encoded), err)
		}
		total += len(page.Entries)
		if page.Cursor == "" {
			break
		}
		cursor = page.Cursor
	}
	if total != 80 {
		t.Fatalf("pagination returned %d entries", total)
	}
}

func formatIndex(index int) string {
	return string([]byte{'0' + byte(index/100), '0' + byte(index/10%10), '0' + byte(index%10)})
}

func TestDirectoryRejectsTraversalAndEscapingSymlinks(t *testing.T) {
	drive := t.TempDir()
	outside := t.TempDir()
	if err := os.Symlink(outside, filepath.Join(drive, "escape")); err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{"../x", "/../x", "/a//b", "/a/./b", "/a/", "/a\\b", "/nul\x00"} {
		result := listDirectory(drive, directoryRequest{Request: strings.Repeat("a", 32), Path: path})
		if result.Status != 400 {
			t.Fatalf("%q accepted: %+v", path, result)
		}
	}
	result := listDirectory(drive, directoryRequest{Request: strings.Repeat("a", 32), Path: "/escape"})
	if result.Status == 200 {
		t.Fatal("escaping symlink opened")
	}
}
