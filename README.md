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
```

## Requirements

- Node.js 18+
- Python 3 available as `python3`

## Commands

### Upload

```bash
npx @ideaforceai/agentcadia-tools upload \
  --task-id <taskId> \
  --origin <origin> \
  --workspace <workspacePath> \
  --metadata-file <metadataJsonPath>
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
