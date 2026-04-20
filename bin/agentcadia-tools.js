#!/usr/bin/env node
const { spawnSync } = require('node:child_process');
const { resolve } = require('node:path');

const script = resolve(__dirname, '../scripts/agentcadia_tools.py');
const args = process.argv.slice(2);
const firstArg = args[0];

if (
  args.length === 0 ||
  firstArg === '--help' ||
  firstArg === '-h' ||
  firstArg === 'help'
) {
  console.log([
    'Agentcadia Tools',
    '',
    'Usage:',
    '  agentcadia-tools <upload|download|eval> [args...]',
    '',
    'Examples:',
    '  agentcadia-tools upload --help',
    '  agentcadia-tools download --help',
    '  agentcadia-tools eval start --help',
    '',
    'This CLI is a thin Node wrapper around scripts/agentcadia_tools.py.',
    'Python 3 must be available as `python3` in PATH.'
  ].join('\n'));
  process.exit(0);
}

const result = spawnSync('python3', [script, ...args], { stdio: 'inherit' });

if (result.error) {
  console.error(`Failed to launch python3: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 1);
