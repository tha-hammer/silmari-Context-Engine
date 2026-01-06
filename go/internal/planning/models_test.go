package planning

import (
	"encoding/json"
	"errors"
	"strings"
	"testing"
)

func TestRequirementNodeValidation(t *testing.T) {
	tests := []struct {
		name    string
		node    *RequirementNode
		wantErr bool
		errMsg  string
	}{
		{
			name: "valid parent node",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "Parent requirement",
				Type:        "parent",
			},
			wantErr: false,
		},
		{
			name: "valid sub_process node",
			node: &RequirementNode{
				ID:          "REQ_000.1",
				Description: "Sub-process requirement",
				Type:        "sub_process",
				ParentID:    "REQ_000",
			},
			wantErr: false,
		},
		{
			name: "valid implementation node",
			node: &RequirementNode{
				ID:          "REQ_000.1.1",
				Description: "Implementation detail",
				Type:        "implementation",
				ParentID:    "REQ_000.1",
				Category:    "functional",
			},
			wantErr: false,
		},
		{
			name: "invalid type",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "Test",
				Type:        "invalid_type",
			},
			wantErr: true,
			errMsg:  "invalid requirement type",
		},
		{
			name: "empty description",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "",
				Type:        "parent",
			},
			wantErr: true,
			errMsg:  "description cannot be empty",
		},
		{
			name: "whitespace description",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "   ",
				Type:        "parent",
			},
			wantErr: true,
			errMsg:  "description cannot be empty",
		},
		{
			name: "invalid category",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "Test",
				Type:        "parent",
				Category:    "invalid_category",
			},
			wantErr: true,
			errMsg:  "invalid category",
		},
		{
			name: "valid with testable properties",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "Test",
				Type:        "parent",
				TestableProperties: []*TestableProperty{
					{Criterion: "must work", PropertyType: "invariant"},
				},
			},
			wantErr: false,
		},
		{
			name: "invalid testable property type",
			node: &RequirementNode{
				ID:          "REQ_000",
				Description: "Test",
				Type:        "parent",
				TestableProperties: []*TestableProperty{
					{Criterion: "must work", PropertyType: "invalid"},
				},
			},
			wantErr: true,
			errMsg:  "invalid property type",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.node.Validate()
			if tt.wantErr {
				if err == nil {
					t.Error("expected error but got nil")
				} else if !strings.Contains(err.Error(), tt.errMsg) {
					t.Errorf("expected error containing %q, got %q", tt.errMsg, err.Error())
				}
			} else {
				if err != nil {
					t.Errorf("unexpected error: %v", err)
				}
			}
		})
	}
}

func TestRequirementNodeHierarchy(t *testing.T) {
	parent := &RequirementNode{
		ID:          "REQ_000",
		Description: "Parent",
		Type:        "parent",
	}

	child1 := &RequirementNode{
		ID:          "REQ_000.1",
		Description: "Child 1",
		Type:        "sub_process",
	}

	child2 := &RequirementNode{
		ID:          "REQ_000.2",
		Description: "Child 2",
		Type:        "sub_process",
	}

	// Test AddChild
	parent.AddChild(child1)
	if child1.ParentID != "REQ_000" {
		t.Errorf("AddChild did not set parent_id: got %q, want %q", child1.ParentID, "REQ_000")
	}
	if len(parent.Children) != 1 {
		t.Errorf("AddChild did not add child: got %d children, want 1", len(parent.Children))
	}

	parent.AddChild(child2)
	if len(parent.Children) != 2 {
		t.Errorf("AddChild did not add second child: got %d children, want 2", len(parent.Children))
	}

	// Test GetByID
	found := parent.GetByID("REQ_000")
	if found != parent {
		t.Error("GetByID did not find parent")
	}

	found = parent.GetByID("REQ_000.1")
	if found != child1 {
		t.Error("GetByID did not find child1")
	}

	found = parent.GetByID("REQ_999")
	if found != nil {
		t.Error("GetByID should return nil for non-existent ID")
	}

	// Test NextChildID
	nextID := parent.NextChildID()
	if nextID != "REQ_000.3" {
		t.Errorf("NextChildID: got %q, want %q", nextID, "REQ_000.3")
	}
}

func TestRequirementHierarchy(t *testing.T) {
	h := NewRequirementHierarchy()

	// Test initial state
	if len(h.Requirements) != 0 {
		t.Errorf("new hierarchy should be empty: got %d requirements", len(h.Requirements))
	}

	// Test NextTopLevelID
	id := h.NextTopLevelID()
	if id != "REQ_000" {
		t.Errorf("NextTopLevelID: got %q, want %q", id, "REQ_000")
	}

	// Test AddRequirement
	req1 := &RequirementNode{
		ID:          "REQ_000",
		Description: "First requirement",
		Type:        "parent",
	}
	h.AddRequirement(req1)

	if len(h.Requirements) != 1 {
		t.Errorf("AddRequirement: got %d requirements, want 1", len(h.Requirements))
	}

	id = h.NextTopLevelID()
	if id != "REQ_001" {
		t.Errorf("NextTopLevelID after add: got %q, want %q", id, "REQ_001")
	}

	// Test AddChild
	child := &RequirementNode{
		ID:          "REQ_000.1",
		Description: "Child requirement",
		Type:        "sub_process",
	}
	err := h.AddChild("REQ_000", child)
	if err != nil {
		t.Errorf("AddChild failed: %v", err)
	}
	if child.ParentID != "REQ_000" {
		t.Errorf("AddChild did not set parent_id: got %q", child.ParentID)
	}

	// Test AddChild with non-existent parent
	err = h.AddChild("REQ_999", child)
	if err == nil {
		t.Error("AddChild should fail for non-existent parent")
	}

	// Test GetByID
	found := h.GetByID("REQ_000")
	if found != req1 {
		t.Error("GetByID did not find top-level requirement")
	}

	found = h.GetByID("REQ_000.1")
	if found != child {
		t.Error("GetByID did not find nested requirement")
	}

	found = h.GetByID("REQ_999")
	if found != nil {
		t.Error("GetByID should return nil for non-existent ID")
	}

	// Test NextChildID
	nextID, err := h.NextChildID("REQ_000")
	if err != nil {
		t.Errorf("NextChildID failed: %v", err)
	}
	if nextID != "REQ_000.2" {
		t.Errorf("NextChildID: got %q, want %q", nextID, "REQ_000.2")
	}

	_, err = h.NextChildID("REQ_999")
	if err == nil {
		t.Error("NextChildID should fail for non-existent parent")
	}
}

func TestRequirementHierarchyValidation(t *testing.T) {
	h := NewRequirementHierarchy()

	// Valid hierarchy
	h.AddRequirement(&RequirementNode{
		ID:          "REQ_000",
		Description: "Valid",
		Type:        "parent",
	})

	err := h.Validate()
	if err != nil {
		t.Errorf("valid hierarchy should not error: %v", err)
	}

	// Add invalid node
	h.AddRequirement(&RequirementNode{
		ID:          "REQ_001",
		Description: "",
		Type:        "parent",
	})

	err = h.Validate()
	if err == nil {
		t.Error("hierarchy with invalid node should error")
	}
}

func TestRequirementHierarchyJSON(t *testing.T) {
	h := NewRequirementHierarchy()
	h.Metadata["source"] = "test"

	req := &RequirementNode{
		ID:          "REQ_000",
		Description: "Test requirement",
		Type:        "parent",
		Category:    "functional",
		Implementation: &ImplementationComponents{
			Backend: []string{"api.go", "handler.go"},
		},
	}
	h.AddRequirement(req)

	child := &RequirementNode{
		ID:          "REQ_000.1",
		Description: "Child requirement",
		Type:        "sub_process",
		AcceptanceCriteria: []string{
			"Must validate input",
			"Must return error on failure",
		},
	}
	req.AddChild(child)

	// Serialize
	data, err := h.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}

	// Deserialize
	h2, err := FromJSON(data)
	if err != nil {
		t.Fatalf("FromJSON failed: %v", err)
	}

	// Verify structure
	if len(h2.Requirements) != 1 {
		t.Errorf("deserialized hierarchy has wrong requirement count: %d", len(h2.Requirements))
	}

	req2 := h2.Requirements[0]
	if req2.ID != "REQ_000" {
		t.Errorf("deserialized requirement has wrong ID: %s", req2.ID)
	}
	if req2.Description != "Test requirement" {
		t.Errorf("deserialized requirement has wrong description: %s", req2.Description)
	}
	if req2.Implementation == nil || len(req2.Implementation.Backend) != 2 {
		t.Error("deserialized requirement lost implementation components")
	}

	if len(req2.Children) != 1 {
		t.Errorf("deserialized requirement has wrong child count: %d", len(req2.Children))
	}

	child2 := req2.Children[0]
	if child2.ParentID != "REQ_000" {
		t.Errorf("deserialized child has wrong parent_id: %s", child2.ParentID)
	}
	if len(child2.AcceptanceCriteria) != 2 {
		t.Errorf("deserialized child has wrong acceptance criteria count: %d", len(child2.AcceptanceCriteria))
	}
}

func TestTestableProperty(t *testing.T) {
	valid := &TestableProperty{
		Criterion:    "must be idempotent",
		PropertyType: "idempotence",
	}
	if err := valid.Validate(); err != nil {
		t.Errorf("valid property should not error: %v", err)
	}

	invalid := &TestableProperty{
		Criterion:    "test",
		PropertyType: "unknown",
	}
	if err := invalid.Validate(); err == nil {
		t.Error("invalid property type should error")
	}
}

func TestDecompositionError(t *testing.T) {
	err := NewDecompositionError(ErrInvalidJSON, "failed to parse", map[string]interface{}{
		"line": 42,
	})

	if err.Code != ErrInvalidJSON {
		t.Errorf("wrong error code: %s", err.Code)
	}

	errStr := err.Error()
	if !strings.Contains(errStr, "INVALID_JSON") {
		t.Error("error string should contain code")
	}
	if !strings.Contains(errStr, "failed to parse") {
		t.Error("error string should contain message")
	}
	if !strings.Contains(errStr, "42") {
		t.Error("error string should contain details")
	}
}

func TestPipelineResult(t *testing.T) {
	r := NewPipelineResult()
	if !r.Success {
		t.Error("new result should be successful")
	}

	r.SetData("path", "/tmp/test.md")
	r.SetData("items", []string{"a", "b", "c"})

	if r.GetString("path") != "/tmp/test.md" {
		t.Error("GetString failed")
	}

	if r.GetString("nonexistent") != "" {
		t.Error("GetString should return empty for nonexistent key")
	}

	items := r.GetStringSlice("items")
	if len(items) != 3 {
		t.Error("GetStringSlice failed")
	}

	r.SetError(errors.New("test error"))
	if r.Success {
		t.Error("SetError should mark result as failed")
	}
	if r.Error != "test error" {
		t.Error("SetError should set error message")
	}
}

func TestImplementationComponentsJSON(t *testing.T) {
	ic := &ImplementationComponents{
		Frontend: []string{"component.tsx"},
		Backend:  []string{"handler.go", "service.go"},
		Shared:   []string{"types.go"},
	}

	data, err := json.Marshal(ic)
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	var ic2 ImplementationComponents
	if err := json.Unmarshal(data, &ic2); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}

	if len(ic2.Backend) != 2 {
		t.Errorf("wrong backend count: %d", len(ic2.Backend))
	}
	if ic2.Middleware != nil && len(ic2.Middleware) != 0 {
		t.Error("omitempty should exclude empty middleware")
	}
}

func TestValidCategories(t *testing.T) {
	expected := []string{
		"functional",
		"non_functional",
		"security",
		"performance",
		"usability",
		"integration",
	}

	for _, cat := range expected {
		if !ValidCategories[cat] {
			t.Errorf("category %q should be valid", cat)
		}
	}

	if ValidCategories["invalid"] {
		t.Error("invalid category should not be valid")
	}
}

