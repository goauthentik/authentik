package filesystemstore

import (
	"context"
	"os"
	"path"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func createTempSessionFile(t *testing.T, dir string, modTime time.Time) string {
	t.Helper()
	path := filepath.Join(dir, "session_test")
	err := os.WriteFile(path, []byte("session data"), 0600)
	require.NoError(t, err)
	err = os.Chtimes(path, modTime, modTime)
	require.NoError(t, err)
	return path
}

func TestNewStore_PathNotExist(t *testing.T) {
	_, err := NewStore("/invalid_path")
	assert.ErrorIs(t, err, ErrSessionStorePathNotExist)
}

func TestNewStore_PathNotWritable(t *testing.T) {
	storePath := path.Join(os.TempDir(), "test")
	err := os.Mkdir(storePath, 0400)
	require.NoError(t, err)

	_, err = NewStore(storePath)
	assert.ErrorIs(t, err, ErrSessionStoreNoPermission)

	_ = os.RemoveAll(storePath)
}

func TestNewStore(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewStore(tmpDir)
	assert.NoError(t, err)
	assert.NotEmpty(t, store)
}

func TestSessionCleanup_RemovesExpired(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewStore(tmpDir)
	require.NoError(t, err)
	store.Options.MaxAge = 1 // 1 second

	// Create an expired session file
	oldTime := time.Now().Add(-10 * time.Second)
	createTempSessionFile(t, tmpDir, oldTime)

	ctx := context.Background()
	err = store.SessionCleanup(ctx)
	assert.NoError(t, err)

	// File should be deleted
	files, _ := os.ReadDir(tmpDir)
	assert.Empty(t, files)
}

func TestSessionCleanup_PreservesValid(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewStore(tmpDir)
	require.NoError(t, err)
	store.Options.MaxAge = 3600 // 1 hour

	// Create a valid (non-expired) session file
	modTime := time.Now().Add(-10 * time.Second)
	createTempSessionFile(t, tmpDir, modTime)

	ctx := context.Background()
	err = store.SessionCleanup(ctx)
	assert.NoError(t, err)

	// File should still exist
	files, _ := os.ReadDir(tmpDir)
	assert.Len(t, files, 1)
}

func TestSessionCleanup_ContextCancel(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewStore(tmpDir)
	require.NoError(t, err)

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // cancel immediately

	err = store.SessionCleanup(ctx)
	assert.ErrorIs(t, err, context.Canceled)
}

func TestSessionCleanup_AlreadyRunning(t *testing.T) {
	tmpDir := t.TempDir()
	store, err := NewStore(tmpDir)
	require.NoError(t, err)

	// Manually acquire the lock before calling SessionCleanup
	lockPath := path.Join(tmpDir, SessionCleanupLockFileName)
	lockFile, err := os.OpenFile(lockPath, os.O_CREATE|os.O_RDWR, 0600)
	require.NoError(t, err, "failed to create lock file")

	err = syscall.Flock(int(lockFile.Fd()), syscall.LOCK_EX|syscall.LOCK_NB)
	require.NoError(t, err, "failed to acquire lock for test")

	// Run SessionCleanup while lock is held
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	err = store.SessionCleanup(ctx)
	assert.ErrorIs(t, err, ErrSessionCleanupAlreadyRunning)

	// Unlock and clean up
	_ = syscall.Flock(int(lockFile.Fd()), syscall.LOCK_UN)
	_ = lockFile.Close()
	_ = os.Remove(lockPath)
}

func TestPersistentStore_ReusesStore(t *testing.T) {
	tmpDir := t.TempDir()
	store1, err := GetPersistentStore(tmpDir)
	require.NoError(t, err)
	assert.NotNil(t, store1)

	store2, err := GetPersistentStore(tmpDir)
	require.NoError(t, err)
	assert.Equal(t, store1, store2)

	StopPersistentStore()
}

func TestStopPersistentStore(t *testing.T) {
	tmpDir := t.TempDir()
	_, err := GetPersistentStore(tmpDir)
	require.NoError(t, err)
	StopPersistentStore()

	// call again should not panic
	StopPersistentStore()
}
