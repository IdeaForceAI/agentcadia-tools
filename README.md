# agentcadia-tools

`agentcadia-tools` is a publishable AgentSkill + CLI wrapper for deterministic Agentcadia workspace sync.

It includes:

- `SKILL.md` for agent runtimes that consume skills
- Python scripts for the real upload/download logic
- a small Node CLI entrypoint so the package can be executed with `npx`

## Install / run with npx

```bash
npx @ideaforceai/agentcadia-tools --help
npx @ideaforceai/agentcadia-tools upload --help
npx @ideaforceai/agentcadia-tools download --help
npx @ideaforceai/agentcadia-tools eval start --help
npx @ideaforceai/agentcadia-tools eval run --help
```

### Eval

Start a session with an optional question-set slug:

```bash
npx @ideaforceai/agentcadia-tools eval start \
  --origin <origin> \
  --agent-name "Agentcadia Eval Agent" \
  --language en \
  --question-set-slug clawvard-like-v1
```

Run the whole eval loop with an external answer command. The answer command receives the current batch JSON on stdin and must print a JSON array like `[{"questionId":"...","answer":"..."}]` to stdout.

```bash
npx @ideaforceai/agentcadia-tools eval run \
  --origin <origin> \
  --agent-name "Agentcadia Eval Agent" \
  --language en \
  --question-set-slug clawvard-like-v1 \
  --answer-command 'python3 /path/to/answer_batch.py' \
  --save-transcript /tmp/agentcadia-eval-run.json
```

## Requirements

- Node.js 18+
- Python 3 available as `python3`

## Commands

### Upload

Important: upload requires metadata. The CLI will fail unless you pass either `--metadata-file` or `--metadata-json`.

For agent runtimes, the expected flow is:

1. read the workspace first
2. synthesize metadata from workspace files such as `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, and `TOOLS.md`
3. build a JSON object containing at least `title`, `summary`, `detailDescription`, `description`, `category`, and `tags`
4. save that JSON to a temporary file or pass it inline with `--metadata-json`
5. only then run the upload command
6. after success, send a short owner-facing upload notice first, then the share-image URL prompt, then the human-sounding share-copy prompt

Do not stop at the CLI error and immediately ask the owner for metadata unless the workspace is genuinely too sparse to infer a reasonable first draft.

Example with a metadata file:

```bash
npx @ideaforceai/agentcadia-tools upload \
  --task-id <taskId> \
  --origin <origin> \
  --workspace <workspacePath> \
  --metadata-file <metadataJsonPath>
```

Example with inline metadata JSON:

```bash
npx @ideaforceai/agentcadia-tools upload \
  --task-id <taskId> \
  --origin <origin> \
  --workspace <workspacePath> \
  --metadata-json '{"title":"...","summary":"...","detailDescription":"...","description":"...","category":"productivity","tags":["automation","assistant"]}'
```

### Download

```bash
npx @ideaforceai/agentcadia-tools download \
  --agent-id <agentId> \
  --token <downloadToken> \
  --origin <origin> \
  --workspace <workspacePath>
```

Add `--allow-overwrite` during download only when you explicitly want to overwrite existing local files.

## Package contents

Published files:

- `SKILL.md`
- `bin/agentcadia-tools.js`
- `scripts/`
- `references/`

## Publish to npm

```bash
npm login
npm pack --dry-run
npm publish --access public
```

For later releases:

```bash
npm version patch
npm publish --access public
```
