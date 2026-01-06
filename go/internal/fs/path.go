// Package fs provides cross-platform file system operations.
// It wraps path/filepath and os packages for common operations.
package fs

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
)

// PathError wraps an error with path context.
type PathError struct {
	Op   string
	Path string
	Err  error
}

func (e *PathError) Error() string {
	return e.Op + " " + e.Path + ": " + e.Err.Error()
}

func (e *PathError) Unwrap() error {
	return e.Err
}

// Join joins path elements using the OS-specific separator.
// It uses filepath.Join for cross-platform compatibility.
func Join(elem ...string) string {
	return filepath.Join(elem...)
}

// Abs returns an absolute representation of the path.
// If the path is not absolute, it will be joined with the current working directory.
func Abs(path string) (string, error) {
	return filepath.Abs(path)
}

// Clean returns the shortest path name equivalent to path.
// It uses filepath.Clean to normalize paths.
func Clean(path string) string {
	return filepath.Clean(path)
}

// Rel returns a relative path that is lexically equivalent to targpath
// when joined to basepath.
func Rel(basepath, targpath string) (string, error) {
	return filepath.Rel(basepath, targpath)
}

// Base returns the last element of path.
func Base(path string) string {
	return filepath.Base(path)
}

// Dir returns all but the last element of path.
func Dir(path string) string {
	return filepath.Dir(path)
}

// Ext returns the file name extension.
func Ext(path string) string {
	return filepath.Ext(path)
}

// Split splits path immediately following the final separator.
func Split(path string) (dir, file string) {
	return filepath.Split(path)
}

// Glob returns the names of all files matching pattern.
func Glob(pattern string) ([]string, error) {
	return filepath.Glob(pattern)
}

// Match reports whether name matches the shell file name pattern.
func Match(pattern, name string) (bool, error) {
	return filepath.Match(pattern, name)
}

// Exists returns true if the path exists.
func Exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// IsFile returns true if the path exists and is a regular file.
func IsFile(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	return info.Mode().IsRegular()
}

// IsDir returns true if the path exists and is a directory.
func IsDir(path string) bool {
	info, err := os.Stat(path)
	if err != nil {
		return false
	}
	return info.IsDir()
}

// IsSymlink returns true if the path is a symbolic link.
func IsSymlink(path string) bool {
	info, err := os.Lstat(path)
	if err != nil {
		return false
	}
	return info.Mode()&os.ModeSymlink != 0
}

// MkdirAll creates a directory named path, along with any necessary parents.
// The permission bits are set to 0755 by default.
func MkdirAll(path string, perm ...os.FileMode) error {
	mode := os.FileMode(0755)
	if len(perm) > 0 {
		mode = perm[0]
	}
	return os.MkdirAll(path, mode)
}

// Remove removes the named file or empty directory.
func Remove(path string) error {
	return os.Remove(path)
}

// RemoveAll removes path and any children it contains.
func RemoveAll(path string) error {
	return os.RemoveAll(path)
}

// Rename renames (moves) oldpath to newpath.
func Rename(oldpath, newpath string) error {
	return os.Rename(oldpath, newpath)
}

// ReadFile reads the named file and returns the contents.
func ReadFile(path string) ([]byte, error) {
	return os.ReadFile(path)
}

// WriteFile writes data to a file named by path.
// If the file does not exist, WriteFile creates it with mode 0644.
func WriteFile(path string, data []byte, perm ...os.FileMode) error {
	mode := os.FileMode(0644)
	if len(perm) > 0 {
		mode = perm[0]
	}
	return os.WriteFile(path, data, mode)
}

// EvalSymlinks returns the path name after the evaluation of any symbolic links.
func EvalSymlinks(path string) (string, error) {
	return filepath.EvalSymlinks(path)
}

// ExpandHome expands the tilde (~) in a path to the user's home directory.
func ExpandHome(path string) (string, error) {
	if !strings.HasPrefix(path, "~") {
		return path, nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", &PathError{Op: "expand_home", Path: path, Err: err}
	}

	if path == "~" {
		return home, nil
	}

	if strings.HasPrefix(path, "~/") {
		return filepath.Join(home, path[2:]), nil
	}

	// ~otheruser/... is not supported
	return "", &PathError{Op: "expand_home", Path: path, Err: errors.New("~otheruser paths not supported")}
}

// WalkDir walks the file tree rooted at root, calling fn for each file or directory.
// It uses filepath.WalkDir which is more efficient than filepath.Walk.
func WalkDir(root string, fn WalkDirFunc) error {
	return filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		return fn(path, d, err)
	})
}

// WalkDirFunc is the type of function called by WalkDir.
type WalkDirFunc func(path string, d os.DirEntry, err error) error

// SkipDir is used as a return value from WalkDirFuncs to indicate that
// the directory named in the call is to be skipped.
var SkipDir = filepath.SkipDir

// SkipAll is used as a return value from WalkDirFuncs to indicate that
// all remaining files are to be skipped.
var SkipAll = filepath.SkipAll

// ListDir returns a list of files and directories in the given directory.
// It does not recurse into subdirectories.
func ListDir(path string) ([]os.DirEntry, error) {
	return os.ReadDir(path)
}

// ListFiles returns a list of file names in the given directory.
// It does not include subdirectories.
func ListFiles(path string) ([]string, error) {
	entries, err := os.ReadDir(path)
	if err != nil {
		return nil, err
	}

	var files []string
	for _, entry := range entries {
		if !entry.IsDir() {
			files = append(files, entry.Name())
		}
	}
	return files, nil
}

// ListDirs returns a list of subdirectory names in the given directory.
func ListDirs(path string) ([]string, error) {
	entries, err := os.ReadDir(path)
	if err != nil {
		return nil, err
	}

	var dirs []string
	for _, entry := range entries {
		if entry.IsDir() {
			dirs = append(dirs, entry.Name())
		}
	}
	return dirs, nil
}

// CopyFile copies a file from src to dst.
func CopyFile(src, dst string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return &PathError{Op: "copy", Path: src, Err: err}
	}

	info, err := os.Stat(src)
	if err != nil {
		return &PathError{Op: "copy", Path: src, Err: err}
	}

	if err := os.WriteFile(dst, data, info.Mode()); err != nil {
		return &PathError{Op: "copy", Path: dst, Err: err}
	}

	return nil
}

// Touch creates an empty file or updates its modification time.
func Touch(path string) error {
	if Exists(path) {
		now := currentTime()
		return os.Chtimes(path, now, now)
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	return f.Close()
}

// Cwd returns the current working directory.
func Cwd() (string, error) {
	return os.Getwd()
}

// Chdir changes the current working directory.
func Chdir(dir string) error {
	return os.Chdir(dir)
}

// Size returns the size of the file in bytes.
// Returns -1 if the file does not exist or cannot be accessed.
func Size(path string) int64 {
	info, err := os.Stat(path)
	if err != nil {
		return -1
	}
	return info.Size()
}

// IsAbs reports whether the path is absolute.
func IsAbs(path string) bool {
	return filepath.IsAbs(path)
}

// ToSlash returns the result of replacing each separator character in path
// with a slash ('/') character.
func ToSlash(path string) string {
	return filepath.ToSlash(path)
}

// FromSlash returns the result of replacing each slash ('/') character in path
// with a separator character.
func FromSlash(path string) string {
	return filepath.FromSlash(path)
}

// SplitList splits a list of paths joined by the OS-specific ListSeparator.
func SplitList(path string) []string {
	return filepath.SplitList(path)
}

// VolumeName returns leading volume name.
// Given "C:\foo\bar" it returns "C:" on Windows.
// Given "\\host\share\foo" it returns "\\host\share".
// On other platforms it returns "".
func VolumeName(path string) string {
	return filepath.VolumeName(path)
}
