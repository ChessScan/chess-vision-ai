# ChessVision Parallel Agent System
**Author:** Trace  
**Purpose:** Working multi-agent setup for CV-001 project  
**Architecture:** ACP Direct (acpx CLI) with shared knowledge workspace

---

## 🎯 AGENT ROLES

### Agent 1: Data Synthesis Agent (codex-data)
**Task:** Generate synthetic training images using Blender
**Focus:** 1000 shallow-angle renders, wood textures, piece variations
**Output:** `/workspace/data/synthetic_renders/*.png`
**Check-in:** Every 50 images

### Agent 2: Model Training Agent (codex-train)
**Task:** YOLO board detection + piece classification
**Focus:** Train on synthetic + real dataset
**Output:** Trained model weights
**Check-in:** Per epoch

### Agent 3: App Dev Agent (codex-app)
**Task:** Complete Flutter app (Analysis screen + game export)
**Focus:** UI polish, PGN export, integration
**Output:** Working mobile app
**Check-in:** Per screen completion

### Agent 4: CV Pipeline Agent (codex-cv)
**Task:** Computer vision pipeline integration
**Focus:** Board detection → move tracking → FEN generation
**Output:** CV pipeline module
**Check-in:** Per stage completion

---

## 📁 SHARED KNOWLEDGE WORKSPACE

```
/workspace/
├── agents/
│   ├── data-agent/          # Agent 1 workspace
│   ├── train-agent/         # Agent 2 workspace
│   ├── app-agent/           # Agent 3 workspace
│   └── cv-agent/            # Agent 4 workspace
├── shared/                  # Central knowledge base
│   ├── spec/               # Technical specifications
│   ├── datasets/           # Training data (all agents contribute)
│   ├── models/             # Trained models
│   ├── results/            # Experiment results
│   └── decisions/          # Architecture decisions
└── coordinator/
    ├── tasks/              # Task assignments
    ├── status/             # Agent status reports
    └── sync/               # Sync points
```

---

## 🔄 WORKFLOW

### Phase 1: Bootstrap (Now)
1. Create shared workspace structure
2. Spawn all 4 agents
3. Distribute initial tasks

### Phase 2: Parallel Execution
1. Agents work independently
2. Write results to shared workspace
3. Report status to coordinator

### Phase 3: Integration (Checkpoint)
1. Collect all outputs
2. Validate against CV-001 goals
3. Merge into main repos

---

## 📝 AGENT COMMUNICATION PROTOCOL

**Status File:** `coordinator/status/{agent-name}.json`
```json
{
  "agent": "codex-data",
  "status": "running",  // running|complete|error|blocked
  "progress": 45,  // percentage
  "lastOutput": "Generated image 450/1000",
  "lastUpdate": "2026-03-28T16:15:00Z",
  "blockers": [],
  "nextCheckpoint": "Image 500"
}
```

**Task File:** `coordinator/tasks/{agent-name}.md`
- Current task description
- Success criteria
- Deadline

---

## 🚀 SPAWN COMMANDS

**Using acpx direct path (working method):**

```bash
# Agent 1: Data Synthesis
./extensions/acpx/node_modules/.bin/acpx codex sessions new --name cv-data-agent
./extensions/acpx/node_modules/.bin/acpx codex -s cv-data-agent --cwd /workspace/agents/data-agent "Generate 1000 training images using Blender. See shared/spec/blender_setup.md"

# Agent 2: Model Training  
./extensions/acpx/node_modules/.bin/acpx codex sessions new --name cv-train-agent
./extensions/acpx/node_modules/.bin/acpx codex -s cv-train-agent --cwd /workspace/agents/train-agent "Set up YOLO training pipeline. See shared/spec/training_specs.md"

# Agent 3: App Dev
./extensions/acpx/node_modules/.bin/acpx codex sessions new --name cv-app-agent
./extensions/acpx/node_modules/.bin/acpx codex -s cv-app-agent --cwd /workspace/agents/app-agent "Complete Flutter app. See shared/spec/app_requirements.md"

# Agent 4: CV Pipeline
./extensions/acpx/node_modules/.bin/acpx codex sessions new --name cv-cv-agent
./extensions/acpx/node_modules/.bin/acpx codex -s cv-cv-agent --cwd /workspace/agents/cv-agent "Build CV pipeline: board detection → FEN. See shared/spec/cv_pipeline.md"
```

---

## 🗺️ KNOWLEDGE CONCENTRATION

**All agents write to shared/, read from shared/:**

- **Input sources:** shared/spec/*
- **Output targets:** shared/{datasets,models,results}/*
- **Status updates:** coordinator/status/*
- **Decisions:** shared/decisions/YYYY-MM-DD_*.md

**Coordinator (Trace) responsibilities:**
1. Monitor all agent status files
2. Detect blockers
3. Resolve conflicts
4. Merge completed work
5. Report to CEO (@jan10010)

---

## ⚡ ADVANTAGES OF THIS SETUP

1. **Works with current OpenClaw** - Uses acpx CLI, not session visibility
2. **Persistent sessions** - Agents keep working independently
3. **Shared knowledge** - All agents access central workspace
4. **No single point of failure** - One agent down doesn't block others
5. **Parallel execution** - All 4 agents run simultaneously
6. **Trackable progress** - Status files provide visibility

---

## 🎯 IMMEDIATE ACTIONS

1. Create workspace structure
2. Write spec files for each agent
3. Spawn all 4 agents
4. Begin parallel execution
5. Monitor every 10 minutes

**Estimated time to first results: 15 minutes**

---

*Design ready for execution. CEO authorization to proceed with spawn?*
