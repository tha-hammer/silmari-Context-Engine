package fs

import (
	"os"
	"path/filepath"
	"testing"
)

func TestJoin(t *testing.T) {
	tests := []struct {
		elem []string
		want string
	}{
		{[]string{"a", "b", "c"}, filepath.Join("a", "b", "c")},
		{[]string{"/a", "b"}, filepath.Join("/a", "b")},
		{[]string{"", "a"}, "a"},
		{[]string{"a"}, "a"},
		{[]string{}, ""},
	}

	for _, tt := range tests {
		got := Join(tt.elem...)
		if got != tt.want {
			t.Errorf("Join(%v) = %q, want %q", tt.elem, got, tt.want)
		}
	}
}

func TestAbs(t *testing.T) {
	// Get current directory for comparison
	cwd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}

	// Test relative path
	got, err := Abs("test")
	if err != nil {
		t.Fatalf("Abs(test) failed: %v", err)
	}
	want := filepath.Join(cwd, "test")
	if got != want {
		t.Errorf("Abs(test) = %q, want %q", got, want)
	}

	// Test absolute path stays the same
	absPath := "/tmp/test"
	got, err = Abs(absPath)
	if err != nil {
		t.Fatalf("Abs(%s) failed: %v", absPath, err)
	}
	if got != absPath && !filepath.IsAbs(got) {
		t.Errorf("Abs(%s) = %q, want absolute path", absPath, got)
	}
}

func TestClean(t *testing.T) {
	tests := []struct {
		path string
		want string
	}{
		{"a/b/../c", filepath.Clean("a/b/../c")},
		{"a//b", filepath.Clean("a//b")},
		{"./a", filepath.Clean("./a")},
		{"", "."},
	}

	for _, tt := range tests {
		got := Clean(tt.path)
		if got != tt.want {
			t.Errorf("Clean(%q) = %q, want %q", tt.path, got, tt.want)
		}
	}
}

func TestBase(t *testing.T) {
	tests := []struct {
		path string
		want string
	}{
		{"/a/b/c", "c"},
		{"a/b/c", "c"},
		{"/", "/"},
		{"", "."},
	}

	for _, tt := range tests {
		got := Base(tt.path)
		if got != tt.want {
			t.Errorf("Base(%q) = %q, want %q", tt.path, got, tt.want)
		}
	}
}

func TestDir(t *testing.T) {
	tests := []struct {
		path string
		want string
	}{
		{"/a/b/c", "/a/b"},
		{"a/b/c", "a/b"},
		{"/", "/"},
	}

	for _, tt := range tests {
		got := Dir(tt.path)
		if got != tt.want {
			t.Errorf("Dir(%q) = %q, want %q", tt.path, got, tt.want)
		}
	}
}

func TestExt(t *testing.T) {
	tests := []struct {
		path string
		want string
	}{
		{"file.txt", ".txt"},
		{"file.tar.gz", ".gz"},
		{"file", ""},
		{".gitignore", ".gitignore"}, // Go treats .gitignore as extension (no base name before dot)
		{".hidden.txt", ".txt"},
	}

	for _, tt := range tests {
		got := Ext(tt.path)
		if got != tt.want {
			t.Errorf("Ext(%q) = %q, want %q", tt.path, got, tt.want)
		}
	}
}

func TestExists(t *testing.T) {
	// Create temp file
	f, err := os.CreateTemp("", "test")
	if err != nil {
		t.Fatal(err)
	}
	path := f.Name()
	f.Close()
	defer os.Remove(path)

	if !Exists(path) {
		t.Errorf("Exists(%q) = false, want true", path)
	}

	if Exists("/nonexistent/path/that/does/not/exist") {
		t.Error("Exists(nonexistent) = true, want false")
	}
}

func TestIsFile(t *testing.T) {
	// Create temp file
	f, err := os.CreateTemp("", "test")
	if err != nil {
		t.Fatal(err)
	}
	path := f.Name()
	f.Close()
	defer os.Remove(path)

	if !IsFile(path) {
		t.Errorf("IsFile(%q) = false, want true", path)
	}

	// Create temp dir
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	if IsFile(dir) {
		t.Errorf("IsFile(%q) = true, want false (is directory)", dir)
	}
}

func TestIsDir(t *testing.T) {
	// Create temp dir
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	if !IsDir(dir) {
		t.Errorf("IsDir(%q) = false, want true", dir)
	}

	// Create temp file
	f, err := os.CreateTemp("", "test")
	if err != nil {
		t.Fatal(err)
	}
	path := f.Name()
	f.Close()
	defer os.Remove(path)

	if IsDir(path) {
		t.Errorf("IsDir(%q) = true, want false (is file)", path)
	}
}

func TestMkdirAll(t *testing.T) {
	// Create temp dir for testing
	base, err := os.MkdirTemp("", "testbase")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(base)

	// Create nested directories
	nested := filepath.Join(base, "a", "b", "c")
	if err := MkdirAll(nested); err != nil {
		t.Fatalf("MkdirAll(%q) failed: %v", nested, err)
	}

	if !IsDir(nested) {
		t.Errorf("MkdirAll did not create directory %q", nested)
	}
}

func TestReadWriteFile(t *testing.T) {
	// Create temp dir
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "test.txt")
	content := []byte("hello world")

	if err := WriteFile(path, content); err != nil {
		t.Fatalf("WriteFile failed: %v", err)
	}

	got, err := ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile failed: %v", err)
	}

	if string(got) != string(content) {
		t.Errorf("ReadFile got %q, want %q", got, content)
	}
}

func TestExpandHome(t *testing.T) {
	home, err := os.UserHomeDir()
	if err != nil {
		t.Skip("cannot get home directory")
	}

	tests := []struct {
		path    string
		want    string
		wantErr bool
	}{
		{"~", home, false},
		{"~/test", filepath.Join(home, "test"), false},
		{"/absolute", "/absolute", false},
		{"relative", "relative", false},
		{"~otheruser/test", "", true},
	}

	for _, tt := range tests {
		got, err := ExpandHome(tt.path)
		if (err != nil) != tt.wantErr {
			t.Errorf("ExpandHome(%q) error = %v, wantErr %v", tt.path, err, tt.wantErr)
			continue
		}
		if !tt.wantErr && got != tt.want {
			t.Errorf("ExpandHome(%q) = %q, want %q", tt.path, got, tt.want)
		}
	}
}

func TestListDir(t *testing.T) {
	// Create temp dir with files and subdirs
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	// Create files
	WriteFile(filepath.Join(dir, "file1.txt"), []byte("content"))
	WriteFile(filepath.Join(dir, "file2.txt"), []byte("content"))
	MkdirAll(filepath.Join(dir, "subdir"))

	entries, err := ListDir(dir)
	if err != nil {
		t.Fatalf("ListDir failed: %v", err)
	}

	if len(entries) != 3 {
		t.Errorf("ListDir got %d entries, want 3", len(entries))
	}
}

func TestListFiles(t *testing.T) {
	// Create temp dir with files and subdirs
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	// Create files
	WriteFile(filepath.Join(dir, "file1.txt"), []byte("content"))
	WriteFile(filepath.Join(dir, "file2.txt"), []byte("content"))
	MkdirAll(filepath.Join(dir, "subdir"))

	files, err := ListFiles(dir)
	if err != nil {
		t.Fatalf("ListFiles failed: %v", err)
	}

	if len(files) != 2 {
		t.Errorf("ListFiles got %d files, want 2", len(files))
	}
}

func TestListDirs(t *testing.T) {
	// Create temp dir with files and subdirs
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	// Create files
	WriteFile(filepath.Join(dir, "file1.txt"), []byte("content"))
	MkdirAll(filepath.Join(dir, "subdir1"))
	MkdirAll(filepath.Join(dir, "subdir2"))

	dirs, err := ListDirs(dir)
	if err != nil {
		t.Fatalf("ListDirs failed: %v", err)
	}

	if len(dirs) != 2 {
		t.Errorf("ListDirs got %d dirs, want 2", len(dirs))
	}
}

func TestCopyFile(t *testing.T) {
	// Create temp dir
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	src := filepath.Join(dir, "src.txt")
	dst := filepath.Join(dir, "dst.txt")
	content := []byte("hello world")

	WriteFile(src, content)

	if err := CopyFile(src, dst); err != nil {
		t.Fatalf("CopyFile failed: %v", err)
	}

	got, err := ReadFile(dst)
	if err != nil {
		t.Fatalf("ReadFile dst failed: %v", err)
	}

	if string(got) != string(content) {
		t.Errorf("CopyFile content got %q, want %q", got, content)
	}
}

func TestSize(t *testing.T) {
	// Create temp file with known content
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	path := filepath.Join(dir, "test.txt")
	content := []byte("hello world")
	WriteFile(path, content)

	size := Size(path)
	if size != int64(len(content)) {
		t.Errorf("Size got %d, want %d", size, len(content))
	}

	// Non-existent file
	size = Size("/nonexistent")
	if size != -1 {
		t.Errorf("Size(nonexistent) got %d, want -1", size)
	}
}

func TestIsAbs(t *testing.T) {
	tests := []struct {
		path string
		want bool
	}{
		{"/absolute", true},
		{"relative", false},
		{"./relative", false},
		{"../relative", false},
	}

	for _, tt := range tests {
		got := IsAbs(tt.path)
		if got != tt.want {
			t.Errorf("IsAbs(%q) = %v, want %v", tt.path, got, tt.want)
		}
	}
}

func TestWalkDir(t *testing.T) {
	// Create temp dir with nested structure
	dir, err := os.MkdirTemp("", "testdir")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	MkdirAll(filepath.Join(dir, "a", "b"))
	WriteFile(filepath.Join(dir, "file1.txt"), []byte("content"))
	WriteFile(filepath.Join(dir, "a", "file2.txt"), []byte("content"))
	WriteFile(filepath.Join(dir, "a", "b", "file3.txt"), []byte("content"))

	var paths []string
	err = WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		paths = append(paths, path)
		return nil
	})
	if err != nil {
		t.Fatalf("WalkDir failed: %v", err)
	}

	// Should have: dir, file1.txt, a, a/file2.txt, a/b, a/b/file3.txt
	if len(paths) != 6 {
		t.Errorf("WalkDir found %d paths, want 6", len(paths))
	}
}
