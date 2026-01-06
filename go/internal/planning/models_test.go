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

func TestFeatureValidation(t *testing.T) {
	tests := []struct {
		name    string
		feature Feature
		wantErr bool
		errMsg  string
	}{
		{
			name: "valid feature",
			feature: Feature{
				ID:     "feat-001",
				Name:   "Test Feature",
				Passes: false,
			},
			wantErr: false,
		},
		{
			name: "empty id",
			feature: Feature{
				ID:     "",
				Name:   "Test Feature",
				Passes: false,
			},
			wantErr: true,
			errMsg:  "id cannot be empty",
		},
		{
			name: "empty name",
			feature: Feature{
				ID:     "feat-001",
				Name:   "",
				Passes: false,
			},
			wantErr: true,
			errMsg:  "name cannot be empty",
		},
		{
			name: "blocked without reason",
			feature: Feature{
				ID:        "feat-001",
				Name:      "Test Feature",
				Blocked:   true,
				BlockedBy: []string{"feat-000"},
			},
			wantErr: true,
			errMsg:  "blocked_reason",
		},
		{
			name: "blocked without blocked_by",
			feature: Feature{
				ID:            "feat-001",
				Name:          "Test Feature",
				Blocked:       true,
				BlockedReason: "Waiting for dependency",
			},
			wantErr: true,
			errMsg:  "blocked_by",
		},
		{
			name: "valid blocked feature",
			feature: Feature{
				ID:            "feat-001",
				Name:          "Test Feature",
				Blocked:       true,
				BlockedReason: "Waiting for dependency",
				BlockedBy:     []string{"feat-000"},
			},
			wantErr: false,
		},
		{
			name: "invalid complexity",
			feature: Feature{
				ID:         "feat-001",
				Name:       "Test Feature",
				Complexity: "extreme",
			},
			wantErr: true,
			errMsg:  "invalid complexity",
		},
		{
			name: "valid complexity",
			feature: Feature{
				ID:         "feat-001",
				Name:       "Test Feature",
				Complexity: "high",
			},
			wantErr: false,
		},
		{
			name: "passes and blocked",
			feature: Feature{
				ID:            "feat-001",
				Name:          "Test Feature",
				Passes:        true,
				Blocked:       true,
				BlockedReason: "reason",
				BlockedBy:     []string{"other"},
			},
			wantErr: true,
			errMsg:  "cannot be both passes=true and blocked=true",
		},
		{
			name: "self dependency",
			feature: Feature{
				ID:           "feat-001",
				Name:         "Test Feature",
				Dependencies: []string{"feat-001"},
			},
			wantErr: true,
			errMsg:  "cannot depend on itself",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.feature.Validate()
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

func TestFeatureListBasics(t *testing.T) {
	fl := NewFeatureList()

	if len(fl.Features) != 0 {
		t.Errorf("new feature list should be empty: got %d", len(fl.Features))
	}

	// Add features
	fl.Add(Feature{ID: "feat-001", Name: "Feature 1", Passes: false})
	fl.Add(Feature{ID: "feat-002", Name: "Feature 2", Passes: true})
	fl.Add(Feature{ID: "feat-003", Name: "Feature 3", Blocked: true, BlockedReason: "reason", BlockedBy: []string{"feat-001"}})

	if len(fl.Features) != 3 {
		t.Errorf("expected 3 features, got %d", len(fl.Features))
	}

	// Test GetByID
	f := fl.GetByID("feat-002")
	if f == nil {
		t.Error("GetByID should find feat-002")
	} else if f.Name != "Feature 2" {
		t.Errorf("wrong feature name: %s", f.Name)
	}

	f = fl.GetByID("feat-999")
	if f != nil {
		t.Error("GetByID should return nil for non-existent ID")
	}
}

func TestFeatureListFiltering(t *testing.T) {
	fl := NewFeatureList()
	fl.Add(Feature{ID: "feat-001", Name: "Feature 1", Passes: false})
	fl.Add(Feature{ID: "feat-002", Name: "Feature 2", Passes: true})
	fl.Add(Feature{ID: "feat-003", Name: "Feature 3", Passes: false, Blocked: true, BlockedReason: "reason", BlockedBy: []string{"feat-001"}})
	fl.Add(Feature{ID: "feat-004", Name: "Feature 4", Passes: true})

	// Test GetPending
	pending := fl.GetPending()
	if len(pending) != 1 {
		t.Errorf("expected 1 pending, got %d", len(pending))
	}
	if pending[0].ID != "feat-001" {
		t.Errorf("wrong pending feature: %s", pending[0].ID)
	}

	// Test GetBlocked
	blocked := fl.GetBlocked()
	if len(blocked) != 1 {
		t.Errorf("expected 1 blocked, got %d", len(blocked))
	}
	if blocked[0].ID != "feat-003" {
		t.Errorf("wrong blocked feature: %s", blocked[0].ID)
	}

	// Test GetCompleted
	completed := fl.GetCompleted()
	if len(completed) != 2 {
		t.Errorf("expected 2 completed, got %d", len(completed))
	}
}

func TestFeatureListStats(t *testing.T) {
	fl := NewFeatureList()
	fl.Add(Feature{ID: "feat-001", Name: "Feature 1", Passes: false})
	fl.Add(Feature{ID: "feat-002", Name: "Feature 2", Passes: true})
	fl.Add(Feature{ID: "feat-003", Name: "Feature 3", Passes: false, Blocked: true, BlockedReason: "reason", BlockedBy: []string{"feat-001"}})

	stats := fl.Stats()
	if stats["total"] != 3 {
		t.Errorf("wrong total: %d", stats["total"])
	}
	if stats["completed"] != 1 {
		t.Errorf("wrong completed: %d", stats["completed"])
	}
	if stats["remaining"] != 2 {
		t.Errorf("wrong remaining: %d", stats["remaining"])
	}
	if stats["blocked"] != 1 {
		t.Errorf("wrong blocked: %d", stats["blocked"])
	}
}

func TestFeatureListJSON(t *testing.T) {
	fl := NewFeatureList()
	fl.Add(Feature{
		ID:          "feat-001",
		Name:        "Feature 1",
		Description: "Test description",
		Priority:    100,
		Category:    "bugfix",
		Passes:      false,
		Complexity:  "high",
	})
	fl.Add(Feature{
		ID:     "feat-002",
		Name:   "Feature 2",
		Passes: true,
	})

	// Serialize
	data, err := fl.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}

	// Verify JSON structure
	jsonStr := string(data)
	if !strings.Contains(jsonStr, `"features"`) {
		t.Error("JSON should contain features key")
	}
	if !strings.Contains(jsonStr, `"feat-001"`) {
		t.Error("JSON should contain feat-001")
	}

	// Deserialize
	fl2, err := FeatureListFromJSON(data)
	if err != nil {
		t.Fatalf("FeatureListFromJSON failed: %v", err)
	}

	if len(fl2.Features) != 2 {
		t.Errorf("wrong feature count after deserialize: %d", len(fl2.Features))
	}

	f := fl2.GetByID("feat-001")
	if f == nil {
		t.Error("should find feat-001 after deserialize")
	} else {
		if f.Description != "Test description" {
			t.Errorf("wrong description: %s", f.Description)
		}
		if f.Priority != 100 {
			t.Errorf("wrong priority: %d", f.Priority)
		}
		if f.Complexity != "high" {
			t.Errorf("wrong complexity: %s", f.Complexity)
		}
	}
}

func TestFeatureListValidation(t *testing.T) {
	// Valid list
	fl := NewFeatureList()
	fl.Add(Feature{ID: "feat-001", Name: "Feature 1", Dependencies: []string{"feat-002"}})
	fl.Add(Feature{ID: "feat-002", Name: "Feature 2"})

	err := fl.Validate()
	if err != nil {
		t.Errorf("valid list should not error: %v", err)
	}

	// Invalid: dependency not found
	fl2 := NewFeatureList()
	fl2.Add(Feature{ID: "feat-001", Name: "Feature 1", Dependencies: []string{"feat-999"}})

	err = fl2.Validate()
	if err == nil {
		t.Error("should fail when dependency not found")
	} else if !strings.Contains(err.Error(), "not found") {
		t.Errorf("wrong error: %v", err)
	}

	// Invalid: blocked_by not found
	fl3 := NewFeatureList()
	fl3.Add(Feature{ID: "feat-001", Name: "Feature 1", Blocked: true, BlockedReason: "reason", BlockedBy: []string{"feat-999"}})

	err = fl3.Validate()
	if err == nil {
		t.Error("should fail when blocked_by reference not found")
	}
}

func TestEmptyFeatureListJSON(t *testing.T) {
	fl := NewFeatureList()

	data, err := fl.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}

	// Should serialize as {"features": []} not null
	if !strings.Contains(string(data), `"features": []`) {
		t.Errorf("empty list should serialize as {\"features\": []}, got: %s", string(data))
	}

	// Round-trip
	fl2, err := FeatureListFromJSON(data)
	if err != nil {
		t.Fatalf("FeatureListFromJSON failed: %v", err)
	}
	if fl2.Features == nil {
		t.Error("Features should not be nil after deserialize")
	}
}

