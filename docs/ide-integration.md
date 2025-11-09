# IDE Integration for docio

Auto-generate documentation stubs when saving Python files.

## Overview

The `docio` CLI can be integrated with your IDE/editor to automatically generate documentation stub files when you save Python files containing `@docio` decorators.

## VSCode

### Method 1: Run on Save (Recommended)

Add to your `.vscode/settings.json`:

```json
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": "\\.py$",
        "cmd": "docio generate ${file}"
      }
    ]
  }
}
```

**Required extension**: [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave)

### Method 2: Task with Keyboard Shortcut

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Generate docio stubs",
      "type": "shell",
      "command": "docio",
      "args": ["generate", "${file}"],
      "presentation": {
        "echo": true,
        "reveal": "silent",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": []
    }
  ]
}
```

Add to `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+d",
    "command": "workbench.action.tasks.runTask",
    "args": "Generate docio stubs"
  }
]
```

## PyCharm / IntelliJ IDEA

### File Watchers

1. Go to **Settings → Tools → File Watchers**
2. Click **+** to add a new watcher
3. Configure:
   - **Name**: docio generate
   - **File type**: Python
   - **Scope**: Project Files
   - **Program**: `docio` (or full path: `/path/to/venv/bin/docio`)
   - **Arguments**: `generate $FilePath$`
   - **Output paths to refresh**: `$ProjectFileDir$/docs`
   - **Working directory**: `$ProjectFileDir$`
   - **Auto-save edited files**: ✓
   - **Trigger on external changes**: ✗

4. Click **OK**

Now every time you save a `.py` file, docio will generate missing stubs.

### External Tools (Manual Trigger)

1. Go to **Settings → Tools → External Tools**
2. Click **+** to add a new tool
3. Configure:
   - **Name**: Generate docio stubs
   - **Program**: `docio`
   - **Arguments**: `generate $FilePath$`
   - **Working directory**: `$ProjectFileDir$`

4. Right-click any Python file → **External Tools → Generate docio stubs**

## Vim / Neovim

### Using autocmd

Add to your `.vimrc` or `init.vim`:

```vim
augroup docio
  autocmd!
  autocmd BufWritePost *.py silent! !docio generate %
augroup END
```

### Using ALE (Asynchronous Lint Engine)

```vim
let g:ale_fixers = {
\   'python': ['docio'],
\}

function! DocioFixer(buffer) abort
  return {
  \   'command': 'docio generate %t',
  \}
endfunction

call ale#fix#registry#Add('docio', 'DocioFixer', ['python'], 'Generate docio stubs')
```

## Emacs

Add to your `.emacs` or `init.el`:

```elisp
(defun docio-generate ()
  "Generate docio stubs for current buffer."
  (interactive)
  (when (eq major-mode 'python-mode)
    (shell-command (format "docio generate %s" (buffer-file-name)))))

(add-hook 'python-mode-hook
          (lambda ()
            (add-hook 'after-save-hook 'docio-generate nil t)))
```

## Sublime Text

### Using Build Systems

Create `Tools → Build System → New Build System`:

```json
{
  "cmd": ["docio", "generate", "$file"],
  "selector": "source.python",
  "file_regex": "^(.+):(\\d+):(\\d+): (.+)$"
}
```

Save as `docio-generate.sublime-build`.

### Using SublimeOnSave Plugin

Install [SublimeOnSave](https://packagecontrol.io/packages/SublimeOnSave), then add to your user settings:

```json
{
  "on_save": [
    {
      "command": "exec",
      "args": {
        "cmd": ["docio", "generate", "$file"]
      },
      "scope": "source.python"
    }
  ]
}
```

## Atom

Add to your `init.coffee`:

```coffee
atom.workspace.observeTextEditors (editor) ->
  editor.onDidSave ->
    if editor.getGrammar().scopeName is 'source.python'
      {exec} = require 'child_process'
      exec "docio generate #{editor.getPath()}"
```

## Generic Shell Script (Any Editor)

Create a file watcher script `watch-docio.sh`:

```bash
#!/bin/bash

# Watch for Python file changes and generate stubs
inotifywait -m -r -e modify --include '\.py$' src/ |
while read path action file; do
    docio generate "$path$file"
done
```

Make it executable and run in the background:

```bash
chmod +x watch-docio.sh
./watch-docio.sh &
```

**Note**: Requires `inotify-tools` on Linux or `fswatch` on macOS.

## Configuration Options

### Disable Auto-Generation Temporarily

Set environment variable:

```bash
export DOCIO_SKIP_GENERATE=1
```

Or use pre-commit skip:

```bash
SKIP=docio-generate git commit -m "message"
```

### Custom Template

Configure in `pyproject.toml`:

```toml
[tool.docio]
stub_template = """# {name}

Your custom template here.

Use {name} as placeholder.
"""
```

## Troubleshooting

### "docio: command not found"

Ensure docio is installed and in PATH:

```bash
pip install -e .
which docio
```

For IDEs, you may need to specify the full path to the docio executable in your virtual environment.

### Files Not Being Generated

1. Check that the file contains `@docio` decorators
2. Run manually: `docio scan path/to/file.py`
3. Verify `docs/` directory exists
4. Check file permissions

### Performance Issues

For large projects, consider:
- Only enabling for specific directories
- Using manual trigger instead of auto-save
- Adjusting IDE debounce settings

## See Also

- [docio CLI Reference](../README.md#cli-usage)
- [Pre-commit Hooks](../.pre-commit-config.yaml)
