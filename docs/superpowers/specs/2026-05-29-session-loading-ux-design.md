# Session Loading UX: Auto-Detect + Manual Multi-Select

## Problem

Session merge (multi-run concatenation) currently has poor UX:
1. **Silent merge** — picking one `.edf` auto-concatenates all runs without confirmation
2. **No visual feedback** — user can't see which runs were detected
3. **No run selection** — can't pick/deselect specific runs
4. **Batch mode ignores SessionSource** — multi-run detected but not used in pipeline
5. **StreamTab has no Load button** — `_on_load()` exists but is unbound

## Design

### Flow

```
User clicks Load → QFileDialog (ExistingFiles, multi-select)
  ├─ 1 file selected  → find_session_runs() → N>1? → SessionDialog → confirm
  ├─ N files selected → use the list directly (no auto-detect)
  └─ Cancel → do nothing
```

### New Files

**`bci/gui/session_loader.py`** — shared loading logic

```python
class SessionDialog(QDialog):
    """Checkbox list of detected runs + info summary + confirm/cancel.
    
    Layout:
      Title: "Session: S001 — 检测到 4 个 run"
      全选 / 取消全选 buttons
      ☑ S001R04.edf  (QListWidget, ItemIsUserCheckable)
      ☑ S001R06.edf
      ...
      Info bar: "4 runs · 64 channels · 160 Hz · 80000 samples"
      [取消] [确定 (合并 4 个)]
    """
    def __init__(self, detected_runs: List[Path], parent=None): ...
    def selected_runs(self) -> List[Path]: ...

def open_session_files(parent: QWidget) -> List[Path]:
    """Full load flow: file dialog → auto-detect → confirm → return list."""
```

SessionDialog reads only metadata (`preload=False` on first run) for the info bar — no data loading, instant open.

### Modified Files

**`bci/gui/batch_tab.py`**
- `_filepath` → `_filepaths: List[str]`
- `_on_load()` → calls `open_session_files(self)` instead of bare QFileDialog
- `_on_file_loaded(filepath)` → `_on_files_loaded(filepaths: List[str])`
- `_on_run()` → passes `self._filepaths` (not single path) to `BatchWorker`

**`bci/gui/stream_tab.py`**
- Same pattern as BatchTab
- **Add "Load File" button** connected to `_on_load()`

**`bci/gui/worker.py`**: `BatchWorker`
- `__init__(self, filepaths: List[str], config)` — accepts list
- `run()`: if `len(filepaths) > 1` → use `SessionSource` for concatenation; else single file

**`bci/gui/main_window.py`**
- `_on_load()` → `open_session_files(self)` → delegates to current tab's `_on_files_loaded()`

### Test Strategy

New file `bci/tests/test_session_loader.py`:

| Test | Purpose |
|------|---------|
| all runs checked by default | Default state correctness |
| deselect some, selected_runs() returns subset | Checkbox logic |
| deselect all → confirm button disabled | Guard against empty selection |
| info line shows correct metadata | Info bar correctness |

Modified `bci/tests/test_session.py`:

| Test | Purpose |
|------|---------|
| BatchWorker multi-filepath uses SessionSource | Batch multi-run path |
| _on_files_loaded replaces _on_file_loaded | Tab interface change |
