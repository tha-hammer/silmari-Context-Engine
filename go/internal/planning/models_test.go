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

// TestPhaseTypeDefinition tests PhaseType enum definition.
// REQ_007.2: Define PhaseType as iota-based integer type preserving execution order
func TestPhaseTypeDefinition(t *testing.T) {
	// Verify order is preserved
	if PhaseResearch != 0 {
		t.Error("PhaseResearch should be 0")
	}
	if PhaseDecomposition != 1 {
		t.Error("PhaseDecomposition should be 1")
	}
	if PhaseTDDPlanning != 2 {
		t.Error("PhaseTDDPlanning should be 2")
	}
	if PhaseMultiDoc != 3 {
		t.Error("PhaseMultiDoc should be 3")
	}
	if PhaseBeadsSync != 4 {
		t.Error("PhaseBeadsSync should be 4")
	}
	if PhaseImplementation != 5 {
		t.Error("PhaseImplementation should be 5")
	}
}

// TestPhaseTypeString tests String() method.
// REQ_007.2: Implement String() method returning phase names
func TestPhaseTypeString(t *testing.T) {
	tests := []struct {
		phase PhaseType
		want  string
	}{
		{PhaseResearch, "research"},
		{PhaseDecomposition, "decomposition"},
		{PhaseTDDPlanning, "tdd_planning"},
		{PhaseMultiDoc, "multi_doc"},
		{PhaseBeadsSync, "beads_sync"},
		{PhaseImplementation, "implementation"},
	}

	for _, tt := range tests {
		if got := tt.phase.String(); got != tt.want {
			t.Errorf("PhaseType.String() = %v, want %v", got, tt.want)
		}
	}
}

// TestPhaseTypeFromString tests FromString() factory method.
// REQ_007.2: Implement FromString(string) (PhaseType, error) factory method
func TestPhaseTypeFromString(t *testing.T) {
	tests := []struct {
		input   string
		want    PhaseType
		wantErr bool
	}{
		{"research", PhaseResearch, false},
		{"decomposition", PhaseDecomposition, false},
		{"tdd_planning", PhaseTDDPlanning, false},
		{"multi_doc", PhaseMultiDoc, false},
		{"beads_sync", PhaseBeadsSync, false},
		{"implementation", PhaseImplementation, false},
		{"RESEARCH", PhaseResearch, false}, // Case insensitive
		{" research ", PhaseResearch, false}, // Whitespace trimming
		{"invalid", PhaseResearch, true},
		{"", PhaseResearch, true},
	}

	for _, tt := range tests {
		got, err := PhaseTypeFromString(tt.input)
		if (err != nil) != tt.wantErr {
			t.Errorf("PhaseTypeFromString(%q) error = %v, wantErr %v", tt.input, err, tt.wantErr)
			continue
		}
		if !tt.wantErr && got != tt.want {
			t.Errorf("PhaseTypeFromString(%q) = %v, want %v", tt.input, got, tt.want)
		}
	}
}

// TestPhaseTypeNext tests Next() method.
// REQ_007.2: Implement Next() method returning the next phase in sequence
func TestPhaseTypeNext(t *testing.T) {
	tests := []struct {
		phase   PhaseType
		want    PhaseType
		wantErr bool
	}{
		{PhaseResearch, PhaseDecomposition, false},
		{PhaseDecomposition, PhaseTDDPlanning, false},
		{PhaseTDDPlanning, PhaseMultiDoc, false},
		{PhaseMultiDoc, PhaseBeadsSync, false},
		{PhaseBeadsSync, PhaseImplementation, false},
		{PhaseImplementation, PhaseImplementation, true}, // Last phase has no next
	}

	for _, tt := range tests {
		got, err := tt.phase.Next()
		if (err != nil) != tt.wantErr {
			t.Errorf("%v.Next() error = %v, wantErr %v", tt.phase, err, tt.wantErr)
			continue
		}
		if !tt.wantErr && got != tt.want {
			t.Errorf("%v.Next() = %v, want %v", tt.phase, got, tt.want)
		}
	}
}

// TestPhaseTypePrevious tests Previous() method.
// REQ_007.2: Implement Previous() method returning the prior phase
func TestPhaseTypePrevious(t *testing.T) {
	tests := []struct {
		phase   PhaseType
		want    PhaseType
		wantErr bool
	}{
		{PhaseResearch, PhaseResearch, true}, // First phase has no previous
		{PhaseDecomposition, PhaseResearch, false},
		{PhaseTDDPlanning, PhaseDecomposition, false},
		{PhaseMultiDoc, PhaseTDDPlanning, false},
		{PhaseBeadsSync, PhaseMultiDoc, false},
		{PhaseImplementation, PhaseBeadsSync, false},
	}

	for _, tt := range tests {
		got, err := tt.phase.Previous()
		if (err != nil) != tt.wantErr {
			t.Errorf("%v.Previous() error = %v, wantErr %v", tt.phase, err, tt.wantErr)
			continue
		}
		if !tt.wantErr && got != tt.want {
			t.Errorf("%v.Previous() = %v, want %v", tt.phase, got, tt.want)
		}
	}
}

// TestPhaseTypeJSON tests JSON marshaling/unmarshaling.
// REQ_007.2: Implement MarshalJSON() and UnmarshalJSON()
func TestPhaseTypeJSON(t *testing.T) {
	phase := PhaseTDDPlanning
	data, err := json.Marshal(phase)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	if string(data) != `"tdd_planning"` {
		t.Errorf("Marshal() = %s, want %q", data, "tdd_planning")
	}

	var unmarshaled PhaseType
	if err := json.Unmarshal(data, &unmarshaled); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if unmarshaled != phase {
		t.Errorf("Unmarshal() = %v, want %v", unmarshaled, phase)
	}
}

// TestAllPhases tests AllPhases() function.
// REQ_007.2: Implement AllPhases() function returning ordered slice
func TestAllPhases(t *testing.T) {
	phases := AllPhases()
	if len(phases) != 6 {
		t.Errorf("AllPhases() length = %d, want 6", len(phases))
	}

	expected := []PhaseType{
		PhaseResearch,
		PhaseDecomposition,
		PhaseTDDPlanning,
		PhaseMultiDoc,
		PhaseBeadsSync,
		PhaseImplementation,
	}

	for i, phase := range phases {
		if phase != expected[i] {
			t.Errorf("AllPhases()[%d] = %v, want %v", i, phase, expected[i])
		}
	}
}

// TestPhaseStatusDefinition tests PhaseStatus enum definition.
// REQ_007.3: Define PhaseStatus as iota-based integer type
func TestPhaseStatusDefinition(t *testing.T) {
	if StatusPending != 0 {
		t.Error("StatusPending should be 0")
	}
	if StatusInProgress != 1 {
		t.Error("StatusInProgress should be 1")
	}
	if StatusComplete != 2 {
		t.Error("StatusComplete should be 2")
	}
	if StatusFailed != 3 {
		t.Error("StatusFailed should be 3")
	}
}

// TestPhaseStatusString tests String() method.
// REQ_007.3: Implement String() method
func TestPhaseStatusString(t *testing.T) {
	tests := []struct {
		status PhaseStatus
		want   string
	}{
		{StatusPending, "pending"},
		{StatusInProgress, "in_progress"},
		{StatusComplete, "complete"},
		{StatusFailed, "failed"},
	}

	for _, tt := range tests {
		if got := tt.status.String(); got != tt.want {
			t.Errorf("PhaseStatus.String() = %v, want %v", got, tt.want)
		}
	}
}

// TestPhaseStatusFromString tests FromString() factory method.
// REQ_007.3: Implement FromString(string) (PhaseStatus, error)
func TestPhaseStatusFromString(t *testing.T) {
	tests := []struct {
		input   string
		want    PhaseStatus
		wantErr bool
	}{
		{"pending", StatusPending, false},
		{"in_progress", StatusInProgress, false},
		{"complete", StatusComplete, false},
		{"failed", StatusFailed, false},
		{"PENDING", StatusPending, false}, // Case insensitive
		{" pending ", StatusPending, false}, // Whitespace
		{"invalid", StatusPending, true},
	}

	for _, tt := range tests {
		got, err := PhaseStatusFromString(tt.input)
		if (err != nil) != tt.wantErr {
			t.Errorf("PhaseStatusFromString(%q) error = %v, wantErr %v", tt.input, err, tt.wantErr)
			continue
		}
		if !tt.wantErr && got != tt.want {
			t.Errorf("PhaseStatusFromString(%q) = %v, want %v", tt.input, got, tt.want)
		}
	}
}

// TestPhaseStatusIsTerminal tests IsTerminal() method.
// REQ_007.3: Implement IsTerminal() method
func TestPhaseStatusIsTerminal(t *testing.T) {
	tests := []struct {
		status PhaseStatus
		want   bool
	}{
		{StatusPending, false},
		{StatusInProgress, false},
		{StatusComplete, true},
		{StatusFailed, true},
	}

	for _, tt := range tests {
		if got := tt.status.IsTerminal(); got != tt.want {
			t.Errorf("%v.IsTerminal() = %v, want %v", tt.status, got, tt.want)
		}
	}
}

// TestPhaseStatusCanTransitionTo tests state transition validation.
// REQ_007.3: Implement CanTransitionTo() and validate state transitions
func TestPhaseStatusCanTransitionTo(t *testing.T) {
	tests := []struct {
		from PhaseStatus
		to   PhaseStatus
		want bool
	}{
		// Pending can only transition to InProgress
		{StatusPending, StatusInProgress, true},
		{StatusPending, StatusComplete, false},
		{StatusPending, StatusFailed, false},
		{StatusPending, StatusPending, false},

		// InProgress can transition to Complete or Failed
		{StatusInProgress, StatusComplete, true},
		{StatusInProgress, StatusFailed, true},
		{StatusInProgress, StatusPending, false},
		{StatusInProgress, StatusInProgress, false},

		// Failed can transition back to InProgress (retry)
		{StatusFailed, StatusInProgress, true},
		{StatusFailed, StatusPending, false},
		{StatusFailed, StatusComplete, false},
		{StatusFailed, StatusFailed, false},

		// Complete is terminal, no transitions
		{StatusComplete, StatusPending, false},
		{StatusComplete, StatusInProgress, false},
		{StatusComplete, StatusFailed, false},
		{StatusComplete, StatusComplete, false},
	}

	for _, tt := range tests {
		if got := tt.from.CanTransitionTo(tt.to); got != tt.want {
			t.Errorf("%v.CanTransitionTo(%v) = %v, want %v", tt.from, tt.to, got, tt.want)
		}
	}
}

// TestPhaseStatusJSON tests JSON marshaling/unmarshaling.
// REQ_007.3: Implement MarshalJSON() and UnmarshalJSON()
func TestPhaseStatusJSON(t *testing.T) {
	status := StatusInProgress
	data, err := json.Marshal(status)
	if err != nil {
		t.Fatalf("Marshal failed: %v", err)
	}

	if string(data) != `"in_progress"` {
		t.Errorf("Marshal() = %s, want %q", data, "in_progress")
	}

	var unmarshaled PhaseStatus
	if err := json.Unmarshal(data, &unmarshaled); err != nil {
		t.Fatalf("Unmarshal failed: %v", err)
	}

	if unmarshaled != status {
		t.Errorf("Unmarshal() = %v, want %v", unmarshaled, status)
	}
}

// TestPhaseResultCreation tests PhaseResult creation and methods.
// REQ_007.4: Port PhaseResult dataclass with all fields
func TestPhaseResultCreation(t *testing.T) {
	result := NewPhaseResult(PhaseResearch)

	if result.Phase != PhaseResearch {
		t.Errorf("Phase = %v, want %v", result.Phase, PhaseResearch)
	}
	if result.Status != StatusPending {
		t.Errorf("Status = %v, want %v", result.Status, StatusPending)
	}
	if result.StartedAt == nil {
		t.Error("StartedAt should not be nil")
	}
	if len(result.Artifacts) != 0 {
		t.Error("Artifacts should be empty")
	}
	if len(result.Errors) != 0 {
		t.Error("Errors should be empty")
	}
	if result.Metadata == nil {
		t.Error("Metadata should not be nil")
	}
}

// TestPhaseResultComplete tests Complete() method.
// REQ_007.4: Implement IsComplete(), IsFailed(), Complete(), Fail()
func TestPhaseResultComplete(t *testing.T) {
	result := NewPhaseResult(PhaseResearch)

	if result.IsComplete() {
		t.Error("IsComplete() should be false initially")
	}

	result.Complete()

	if !result.IsComplete() {
		t.Error("IsComplete() should be true after Complete()")
	}
	if result.Status != StatusComplete {
		t.Errorf("Status = %v, want %v", result.Status, StatusComplete)
	}
	if result.CompletedAt == nil {
		t.Error("CompletedAt should not be nil")
	}
	if result.DurationSeconds <= 0 {
		t.Error("DurationSeconds should be > 0")
	}
}

// TestPhaseResultFail tests Fail() method.
// REQ_007.4: Implement Fail() method
func TestPhaseResultFail(t *testing.T) {
	result := NewPhaseResult(PhaseResearch)

	if result.IsFailed() {
		t.Error("IsFailed() should be false initially")
	}

	testErr := errors.New("test error")
	result.Fail(testErr)

	if !result.IsFailed() {
		t.Error("IsFailed() should be true after Fail()")
	}
	if result.Status != StatusFailed {
		t.Errorf("Status = %v, want %v", result.Status, StatusFailed)
	}
	if len(result.Errors) != 1 {
		t.Errorf("len(Errors) = %d, want 1", len(result.Errors))
	}
	if !strings.Contains(result.Errors[0], "test error") {
		t.Errorf("Errors[0] = %q, should contain %q", result.Errors[0], "test error")
	}
}

// TestPhaseResultArtifacts tests artifact management.
// REQ_007.4: Include Artifacts []string field
func TestPhaseResultArtifacts(t *testing.T) {
	result := NewPhaseResult(PhaseResearch)

	result.AddArtifact("/path/to/file1.md")
	result.AddArtifact("/path/to/file2.json")

	if len(result.Artifacts) != 2 {
		t.Errorf("len(Artifacts) = %d, want 2", len(result.Artifacts))
	}
	if result.Artifacts[0] != "/path/to/file1.md" {
		t.Errorf("Artifacts[0] = %q, want %q", result.Artifacts[0], "/path/to/file1.md")
	}
}

// TestPhaseResultMetadata tests metadata management.
// REQ_007.4: Include Metadata map[string]interface{}
func TestPhaseResultMetadata(t *testing.T) {
	result := NewPhaseResult(PhaseResearch)

	result.SetMetadata("key1", "value1")
	result.SetMetadata("key2", 42)

	if result.Metadata["key1"] != "value1" {
		t.Errorf("Metadata[key1] = %v, want %q", result.Metadata["key1"], "value1")
	}
	if result.Metadata["key2"] != 42 {
		t.Errorf("Metadata[key2] = %v, want 42", result.Metadata["key2"])
	}
}

// TestPhaseResultToDict tests serialization.
// REQ_007.4: Implement ToDict() for checkpoint serialization
func TestPhaseResultToDict(t *testing.T) {
	result := NewPhaseResult(PhaseResearch)
	result.AddArtifact("/path/to/file.md")
	result.SetMetadata("test", "value")
	result.Complete()

	dict := result.ToDict()

	if dict["phase"] != "research" {
		t.Errorf("dict[phase] = %v, want %q", dict["phase"], "research")
	}
	if dict["status"] != "complete" {
		t.Errorf("dict[status] = %v, want %q", dict["status"], "complete")
	}
	if _, ok := dict["artifacts"]; !ok {
		t.Error("dict should contain artifacts")
	}
	if _, ok := dict["metadata"]; !ok {
		t.Error("dict should contain metadata")
	}
}

// TestPhaseResultFromDict tests deserialization.
// REQ_007.4: Implement FromDict() for deserialization
func TestPhaseResultFromDict(t *testing.T) {
	dict := map[string]interface{}{
		"phase":  "research",
		"status": "complete",
		"artifacts": []interface{}{"/path/to/file.md"},
		"errors": []interface{}{"test error"},
		"duration_seconds": 1.5,
		"metadata": map[string]interface{}{"key": "value"},
	}

	result, err := PhaseResultFromDict(dict)
	if err != nil {
		t.Fatalf("PhaseResultFromDict failed: %v", err)
	}

	if result.Phase != PhaseResearch {
		t.Errorf("Phase = %v, want %v", result.Phase, PhaseResearch)
	}
	if result.Status != StatusComplete {
		t.Errorf("Status = %v, want %v", result.Status, StatusComplete)
	}
	if len(result.Artifacts) != 1 {
		t.Errorf("len(Artifacts) = %d, want 1", len(result.Artifacts))
	}
	if len(result.Errors) != 1 {
		t.Errorf("len(Errors) = %d, want 1", len(result.Errors))
	}
	if result.DurationSeconds != 1.5 {
		t.Errorf("DurationSeconds = %v, want 1.5", result.DurationSeconds)
	}
}

// TestPipelineStateCreation tests PipelineState creation.
// REQ_007.5: Port PipelineState with all fields
func TestPipelineStateCreation(t *testing.T) {
	state, err := NewPipelineState("/test/path", AutonomyCheckpoint)
	if err != nil {
		t.Fatalf("NewPipelineState failed: %v", err)
	}

	if state.ProjectPath != "/test/path" {
		t.Errorf("ProjectPath = %q, want %q", state.ProjectPath, "/test/path")
	}
	if state.AutonomyMode != AutonomyCheckpoint {
		t.Errorf("AutonomyMode = %v, want %v", state.AutonomyMode, AutonomyCheckpoint)
	}
	if state.StartedAt == nil {
		t.Error("StartedAt should not be nil")
	}
	if state.PhaseResults == nil {
		t.Error("PhaseResults should not be nil")
	}
	if state.ContextEntryIDs == nil {
		t.Error("ContextEntryIDs should not be nil")
	}
}

// TestPipelineStateValidation tests project path validation.
// REQ_007.5: Implement validation ensuring non-empty project path
func TestPipelineStateValidation(t *testing.T) {
	_, err := NewPipelineState("", AutonomyCheckpoint)
	if err == nil {
		t.Error("NewPipelineState should fail with empty project path")
	}

	state, _ := NewPipelineState("/test/path", AutonomyCheckpoint)
	err = state.SetProjectPath("")
	if err == nil {
		t.Error("SetProjectPath should fail with empty path")
	}
}

// TestPipelineStatePhaseResults tests phase result management.
// REQ_007.5: Implement GetPhaseResult, SetPhaseResult, IsPhaseComplete
func TestPipelineStatePhaseResults(t *testing.T) {
	state, _ := NewPipelineState("/test/path", AutonomyCheckpoint)

	result := NewPhaseResult(PhaseResearch)
	state.SetPhaseResult(PhaseResearch, result)

	retrieved := state.GetPhaseResult(PhaseResearch)
	if retrieved != result {
		t.Error("GetPhaseResult should return the same result")
	}

	if state.IsPhaseComplete(PhaseResearch) {
		t.Error("IsPhaseComplete should be false for pending phase")
	}

	result.Complete()
	if !state.IsPhaseComplete(PhaseResearch) {
		t.Error("IsPhaseComplete should be true after Complete()")
	}
}

// TestPipelineStateAllPhasesComplete tests completion checking.
// REQ_007.5: Implement AllPhasesComplete()
func TestPipelineStateAllPhasesComplete(t *testing.T) {
	state, _ := NewPipelineState("/test/path", AutonomyCheckpoint)

	if state.AllPhasesComplete() {
		t.Error("AllPhasesComplete should be false initially")
	}

	// Complete all phases
	for _, phase := range AllPhases() {
		result := NewPhaseResult(phase)
		result.Complete()
		state.SetPhaseResult(phase, result)
	}

	if !state.AllPhasesComplete() {
		t.Error("AllPhasesComplete should be true after all phases complete")
	}
}

// TestPipelineStateContextEntries tests CWA tracking.
// REQ_007.5: Implement TrackContextEntry and GetContextEntries
func TestPipelineStateContextEntries(t *testing.T) {
	state, _ := NewPipelineState("/test/path", AutonomyCheckpoint)

	state.TrackContextEntry(PhaseResearch, "entry-1")
	state.TrackContextEntry(PhaseResearch, "entry-2")
	state.TrackContextEntry(PhaseDecomposition, "entry-3")

	entries := state.GetContextEntries(PhaseResearch)
	if len(entries) != 2 {
		t.Errorf("len(GetContextEntries(PhaseResearch)) = %d, want 2", len(entries))
	}

	entries = state.GetContextEntries(PhaseDecomposition)
	if len(entries) != 1 {
		t.Errorf("len(GetContextEntries(PhaseDecomposition)) = %d, want 1", len(entries))
	}
}

// TestPipelineStateToDict tests serialization.
// REQ_007.5: Implement ToDict() and ToCheckpointDict()
func TestPipelineStateToDict(t *testing.T) {
	state, _ := NewPipelineState("/test/path", AutonomyCheckpoint)
	state.CheckpointID = "checkpoint-123"
	state.BeadsEpicID = "epic-456"

	result := NewPhaseResult(PhaseResearch)
	result.Complete()
	state.SetPhaseResult(PhaseResearch, result)

	state.TrackContextEntry(PhaseResearch, "entry-1")

	dict := state.ToDict()

	if dict["project_path"] != "/test/path" {
		t.Errorf("dict[project_path] = %v, want %q", dict["project_path"], "/test/path")
	}
	if dict["autonomy_mode"] != "checkpoint" {
		t.Errorf("dict[autonomy_mode] = %v, want %q", dict["autonomy_mode"], "checkpoint")
	}
	if dict["checkpoint_id"] != "checkpoint-123" {
		t.Errorf("dict[checkpoint_id] = %v, want %q", dict["checkpoint_id"], "checkpoint-123")
	}
	if dict["beads_epic_id"] != "epic-456" {
		t.Errorf("dict[beads_epic_id] = %v, want %q", dict["beads_epic_id"], "epic-456")
	}
}

// TestPipelineStateFromDict tests deserialization.
// REQ_007.5: Implement FromDict() and FromCheckpointDict()
func TestPipelineStateFromDict(t *testing.T) {
	dict := map[string]interface{}{
		"project_path":  "/test/path",
		"autonomy_mode": "batch",
		"checkpoint_id": "checkpoint-123",
		"beads_epic_id": "epic-456",
		"phase_results": map[string]interface{}{
			"research": map[string]interface{}{
				"phase":  "research",
				"status": "complete",
			},
		},
		"context_entry_ids": map[string]interface{}{
			"research": []interface{}{"entry-1", "entry-2"},
		},
	}

	state, err := PipelineStateFromDict(dict)
	if err != nil {
		t.Fatalf("PipelineStateFromDict failed: %v", err)
	}

	if state.ProjectPath != "/test/path" {
		t.Errorf("ProjectPath = %q, want %q", state.ProjectPath, "/test/path")
	}
	if state.AutonomyMode != AutonomyBatch {
		t.Errorf("AutonomyMode = %v, want %v", state.AutonomyMode, AutonomyBatch)
	}
	if state.CheckpointID != "checkpoint-123" {
		t.Errorf("CheckpointID = %q, want %q", state.CheckpointID, "checkpoint-123")
	}

	result := state.GetPhaseResult(PhaseResearch)
	if result == nil {
		t.Fatal("PhaseResult for research should not be nil")
	}
	if result.Status != StatusComplete {
		t.Errorf("PhaseResult.Status = %v, want %v", result.Status, StatusComplete)
	}

	entries := state.GetContextEntries(PhaseResearch)
	if len(entries) != 2 {
		t.Errorf("len(context entries) = %d, want 2", len(entries))
	}
}

// TestPipelineStateSerialization tests full round-trip serialization.
// REQ_007.5: Verify serialization compatibility
func TestPipelineStateSerialization(t *testing.T) {
	state, _ := NewPipelineState("/test/path", AutonomyFullyAutonomous)
	state.CheckpointID = "checkpoint-abc"

	result := NewPhaseResult(PhaseResearch)
	result.AddArtifact("/path/to/artifact.md")
	result.Complete()
	state.SetPhaseResult(PhaseResearch, result)

	state.TrackContextEntry(PhaseResearch, "entry-123")

	// Serialize
	dict := state.ToDict()

	// Deserialize
	restored, err := PipelineStateFromDict(dict)
	if err != nil {
		t.Fatalf("Deserialization failed: %v", err)
	}

	// Verify
	if restored.ProjectPath != state.ProjectPath {
		t.Errorf("ProjectPath mismatch: %q != %q", restored.ProjectPath, state.ProjectPath)
	}
	if restored.AutonomyMode != state.AutonomyMode {
		t.Errorf("AutonomyMode mismatch: %v != %v", restored.AutonomyMode, state.AutonomyMode)
	}
	if restored.CheckpointID != state.CheckpointID {
		t.Errorf("CheckpointID mismatch: %q != %q", restored.CheckpointID, state.CheckpointID)
	}

	restoredResult := restored.GetPhaseResult(PhaseResearch)
	if restoredResult == nil {
		t.Fatal("Restored phase result should not be nil")
	}
	if restoredResult.Status != StatusComplete {
		t.Errorf("Restored status = %v, want %v", restoredResult.Status, StatusComplete)
	}

	restoredEntries := restored.GetContextEntries(PhaseResearch)
	if len(restoredEntries) != 1 {
		t.Errorf("len(restored entries) = %d, want 1", len(restoredEntries))
	}
}
