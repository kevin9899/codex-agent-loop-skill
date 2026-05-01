#!/usr/bin/env node

import { existsSync, promises as fs } from 'node:fs'
import { spawn } from 'node:child_process'
import { dirname, join, resolve } from 'node:path'

const VIEWPOINT_PROFILES = {
  default: [
    'architecture_dependency',
    'failure_verification',
    'goal_efficiency',
    'requirement_alignment',
    'implementation_quality',
  ],
  extended: [
    'architecture_dependency',
    'failure_verification',
    'goal_efficiency',
    'requirement_alignment',
    'implementation_quality',
  ],
}

const VIEWPOINT_FOCUS = {
  architecture_dependency: [
    'map coupling, ownership seams, dependency order, and cross-cutting modules',
    'surface hidden prerequisites or architecture constraints that should change the stage boundary',
  ],
  failure_verification: [
    'look for regression paths, unsafe assumptions, missing checks, and verification blind spots',
    'focus on how the current goal or plan could fail in production or during rollout',
  ],
  goal_efficiency: [
    'search for shorter paths, leverage points, reuse opportunities, and lower-risk sequencing',
    'push against overscope, ceremonial steps, and low-yield work',
  ],
  requirement_alignment: [
    'compare the current state against the explicit user ask, success conditions, and sequential objectives',
    'surface scope drift, missed required behavior, Korean/user-facing copy mismatches, and unclosed acceptance criteria',
  ],
  implementation_quality: [
    'review maintainability, test coverage, error handling, data integrity, and production-readiness risks',
    'focus on whether the implementation can be safely carried forward without hidden cleanup or fragile assumptions',
  ],
}

const VALID_PHASES = new Set([
  'pre_plan',
  'post_stage',
  'goal_reassessment',
  'stop_authorization',
])

const VALID_EFFORTS = new Set([
  'low',
  'medium',
  'high',
  'max',
])

const VALID_VIEWPOINT_PROFILES = new Set(['default', 'extended'])

const DEFAULT_MODEL = process.env.CLAUDE_CODE_HIGHEST_MODEL?.trim() || 'opus'
const DEFAULT_EFFORT = 'max'
const DEFAULT_TIMEOUT_MS = 20 * 60 * 1000
const DEFAULT_BYPASS_PERMISSIONS = process.env.AGENT_LOOP_CLAUDE_BYPASS_PERMISSIONS === '1'

function usage() {
  console.error(
    [
      'Usage:',
      '  node <agent-loop-skill-dir>/scripts/run-claude-research.mjs --workspace <path> [options]',
      '',
      'Required:',
      '  --workspace <path>              Workspace root Claude should inspect',
      '  --goal "<text>"                 Working goal text',
      '  or --goal-file <path>           File whose full contents become the working goal text',
      '',
      'Options:',
      '  --phase <pre_plan|post_stage|goal_reassessment|stop_authorization>   default: pre_plan',
      `  --model <claude-model>          default: ${DEFAULT_MODEL}`,
      `  --effort <low|medium|high|max>  default: ${DEFAULT_EFFORT}`,
      `  --timeout-ms <number>           default: ${DEFAULT_TIMEOUT_MS}`,
      '  --viewpoint-profile <default|extended>  default: default',
      '  --high-difficulty               alias for --viewpoint-profile extended; still capped at 5 lanes',
      '  --context-file <path>           Repeatable. Compact packet or reference file to read first',
      '  --append "<text>"               Repeatable. Extra operator instruction appended to every lane',
      '  --out-dir <path>                Optional output directory',
      '  --dangerously-bypass-permissions  Pass Claude bypassPermissions flags; default is off unless AGENT_LOOP_CLAUDE_BYPASS_PERMISSIONS=1',
      '  --dry-run                       Write prompts/manifest only, do not call Claude',
      '  --help                          Show this message',
    ].join('\n'),
  )
}

function timestampId() {
  const now = new Date()
  const yyyy = now.getFullYear()
  const mm = String(now.getMonth() + 1).padStart(2, '0')
  const dd = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mi = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  return `${yyyy}${mm}${dd}T${hh}${mi}${ss}`
}

function requireValue(argv, index, flag) {
  const value = argv[index + 1]
  if (!value || value.startsWith('--')) {
    throw new Error(`Missing value for ${flag}`)
  }
  return value
}

function parseArgs(argv) {
    const options = {
      phase: 'pre_plan',
      model: DEFAULT_MODEL,
      effort: DEFAULT_EFFORT,
      timeoutMs: DEFAULT_TIMEOUT_MS,
      viewpointProfile: 'default',
      contextFiles: [],
      append: [],
      bypassPermissions: DEFAULT_BYPASS_PERMISSIONS,
      dryRun: false,
  }

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]

    switch (arg) {
      case '--workspace':
        options.workspace = requireValue(argv, index, arg)
        index += 1
        break
      case '--goal':
        options.goal = requireValue(argv, index, arg)
        index += 1
        break
      case '--goal-file':
        options.goalFile = requireValue(argv, index, arg)
        index += 1
        break
      case '--phase': {
        const value = requireValue(argv, index, arg)
        if (!VALID_PHASES.has(value)) {
          throw new Error(`Invalid --phase value: ${value}`)
        }
        options.phase = value
        index += 1
        break
      }
      case '--model':
        options.model = requireValue(argv, index, arg)
        index += 1
        break
      case '--effort': {
        const value = requireValue(argv, index, arg)
        if (!VALID_EFFORTS.has(value)) {
          throw new Error(`Invalid --effort value: ${value}`)
        }
        options.effort = value
        index += 1
        break
      }
      case '--timeout-ms': {
        const raw = requireValue(argv, index, arg)
        const parsed = Number.parseInt(raw, 10)
        if (!Number.isFinite(parsed) || parsed < 1000) {
          throw new Error(`Invalid --timeout-ms value: ${raw}`)
        }
        options.timeoutMs = parsed
        index += 1
        break
      }
      case '--viewpoint-profile': {
        const value = requireValue(argv, index, arg)
        if (!VALID_VIEWPOINT_PROFILES.has(value)) {
          throw new Error(`Invalid --viewpoint-profile value: ${value}`)
        }
        options.viewpointProfile = value
        index += 1
        break
      }
      case '--high-difficulty':
        options.viewpointProfile = 'extended'
        break
      case '--context-file':
        options.contextFiles.push(requireValue(argv, index, arg))
        index += 1
        break
      case '--append':
        options.append.push(requireValue(argv, index, arg))
        index += 1
        break
      case '--out-dir':
        options.outDir = requireValue(argv, index, arg)
        index += 1
        break
      case '--dangerously-bypass-permissions':
        options.bypassPermissions = true
        break
      case '--dry-run':
        options.dryRun = true
        break
      case '--help':
        usage()
        process.exit(0)
      default:
        throw new Error(`Unknown argument: ${arg}`)
    }
  }

  return options
}

function quotePowerShell(value) {
  return `'${value.replace(/'/g, "''")}'`
}

function extractJsonCandidate(text) {
  const trimmed = text.trim()
  if (!trimmed) {
    throw new Error('Claude returned empty output')
  }

  const fenced = trimmed.match(/```(?:json)?\s*([\s\S]+?)```/iu)
  if (fenced?.[1]) {
    return fenced[1].trim()
  }

  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    return trimmed
  }

  const objectStart = trimmed.indexOf('{')
  const objectEnd = trimmed.lastIndexOf('}')
  if (objectStart >= 0 && objectEnd > objectStart) {
    return trimmed.slice(objectStart, objectEnd + 1)
  }

  throw new Error('Claude output did not contain parseable JSON')
}

function normalizeStringArray(value) {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean)
}

function normalizeFindings(value) {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null
      }

      const severity = typeof item.severity === 'string' && ['critical', 'high', 'medium', 'low'].includes(item.severity)
        ? item.severity
        : 'medium'

      const title = typeof item.title === 'string' ? item.title.trim() : ''
      const detail = typeof item.detail === 'string' ? item.detail.trim() : ''
      const evidence = normalizeStringArray(item.evidence)
      const planImplication = typeof item.plan_implication === 'string' ? item.plan_implication.trim() : ''

      if (!title && !detail && evidence.length === 0 && !planImplication) {
        return null
      }

      return {
        severity,
        title,
        detail,
        evidence,
        plan_implication: planImplication,
      }
    })
    .filter(Boolean)
}

function normalizeAutonomousHaltPermission(value) {
  if (!value || typeof value !== 'object') {
    return null
  }

  const decision = typeof value.decision === 'string' && ['allow', 'deny'].includes(value.decision)
    ? value.decision
    : 'deny'

  const reason = typeof value.reason === 'string' ? value.reason.trim() : ''
  const blockingConditions = normalizeStringArray(value.blocking_conditions)
  const requiredEvidence = normalizeStringArray(value.required_evidence)

  if (!reason && blockingConditions.length === 0 && requiredEvidence.length === 0 && !('decision' in value)) {
    return null
  }

  return {
    decision,
    reason,
    blocking_conditions: blockingConditions,
    required_evidence: requiredEvidence,
  }
}

function normalizeLanePayload(payload, viewpoint, phase) {
  if (!payload || typeof payload !== 'object') {
    throw new Error(`Claude lane returned a non-object payload for ${viewpoint}`)
  }

  const confidence = typeof payload.confidence === 'string' && ['high', 'medium', 'low'].includes(payload.confidence)
    ? payload.confidence
    : 'medium'

  const autonomousHaltPermission = normalizeAutonomousHaltPermission(payload.autonomous_halt_permission)
  if (phase === 'stop_authorization' && !autonomousHaltPermission) {
    throw new Error(`Claude lane did not return autonomous_halt_permission for ${viewpoint}`)
  }

  return {
    viewpoint,
    phase,
    summary: typeof payload.summary === 'string' ? payload.summary.trim() : '',
    findings: normalizeFindings(payload.findings),
    recommended_stage_shape: normalizeStringArray(payload.recommended_stage_shape),
    open_questions: normalizeStringArray(payload.open_questions),
    confidence,
    autonomous_halt_permission: autonomousHaltPermission,
  }
}

function buildClaudeArgs(options, viewpoint, extraDirs) {
  const args = [
    '-p',
    '--no-session-persistence',
    '--model',
    options.model,
    '--effort',
    options.effort,
    '--name',
    `agent-loop-${options.phase}-${viewpoint}`,
  ]

  if (options.bypassPermissions) {
    args.push('--permission-mode', 'bypassPermissions', '--dangerously-skip-permissions')
  }

  for (const dir of extraDirs) {
    args.push('--add-dir', dir)
  }

  return args
}

function buildPrompt(options, viewpoint, contextFiles) {
  const focus = VIEWPOINT_FOCUS[viewpoint]
  const laneCount = options.viewpoints.length
  const isStopAuthorization = options.phase === 'stop_authorization'
  const contextBlock = contextFiles.length > 0
    ? [
        'Read these context files first before wider inspection:',
        ...contextFiles.map((filePath) => `- ${filePath}`),
      ].join('\n')
    : 'No extra context files were supplied. Read the workspace contract files first, then inspect the codebase directly.'

  const extraInstructions = options.append.length > 0
    ? [
        '',
        'Operator addenda:',
        ...options.append.map((line) => `- ${line}`),
      ].join('\n')
    : ''

  const missionLines = isStopAuthorization
    ? [
        '- inspect whether the orchestrator may autonomously halt the live invocation now',
        '- decide only your lane-level halt verdict; do not speak for other lanes',
        '- default to deny if evidence is missing, if continuing is still cheap and safe, or if human authority is required',
      ]
    : [
        '- produce read-only research that sharpens the Codex orchestrator’s plan or reassessment',
        '- work independently; do not try to simulate the other viewpoints',
        '- do not decide stop/continue or emit a final orchestration decision',
      ]

  const phaseSpecificRules = isStopAuthorization
    ? [
        '- treat any missing handoff, unclear pause/stop basis, or incomplete required work as a deny signal',
        '- require explicit file-backed evidence for an allow decision',
        '- do not infer allow from silence, optimism, or another lane eventually agreeing with you',
      ]
    : []

  const returnShape = isStopAuthorization
    ? [
        '{',
        '  "viewpoint": "<same viewpoint string>",',
        '  "phase": "<same phase string>",',
        '  "summary": "<2-4 sentence compact summary>",',
        '  "findings": [',
        '    {',
        '      "severity": "critical|high|medium|low",',
        '      "title": "<short title>",',
        '      "detail": "<why this matters>",',
        '      "evidence": ["<path or direct observation>", "<path or direct observation>"],',
        '      "plan_implication": "<how the orchestrator should continue, pause, or deny halt>"',
        '    }',
        '  ],',
        '  "recommended_stage_shape": ["<what should happen next if halt is denied>", "<what should happen next if halt is denied>"],',
        '  "open_questions": ["<explicit unknown>", "<explicit unknown>"],',
        '  "confidence": "high|medium|low",',
        '  "autonomous_halt_permission": {',
        '    "decision": "allow|deny",',
        '    "reason": "<why halting now is or is not allowed>",',
        '    "blocking_conditions": ["<why halting must be denied or what work remains>", "<why halting must be denied or what work remains>"],',
        '    "required_evidence": ["<path or direct observation>", "<path or direct observation>"]',
        '  }',
        '}',
      ]
    : [
        '{',
        '  "viewpoint": "<same viewpoint string>",',
        '  "phase": "<same phase string>",',
        '  "summary": "<2-4 sentence compact summary>",',
        '  "findings": [',
        '    {',
        '      "severity": "critical|high|medium|low",',
        '      "title": "<short title>",',
        '      "detail": "<why this matters>",',
        '      "evidence": ["<path or direct observation>", "<path or direct observation>"],',
        '      "plan_implication": "<how the plan or stage boundary should change>"',
        '    }',
        '  ],',
        '  "recommended_stage_shape": ["<stage or ordering recommendation>", "<stage or ordering recommendation>"],',
        '  "open_questions": ["<explicit unknown>", "<explicit unknown>"],',
        '  "confidence": "high|medium|low"',
        '}',
      ]

  return [
    `You are one of ${laneCount} independent Claude research contributors for the personal Codex \`$loop\` skill.`,
    `Research phase: ${options.phase}.`,
    `Assigned viewpoint: ${viewpoint}.`,
    `Viewpoint profile: ${options.viewpointProfile}.`,
    `Workspace root: ${options.workspace}.`,
    '',
    'Mission:',
    ...missionLines,
    '',
    'Mandatory operating rules:',
    '- read AGENTS.md, CLAUDE.md, or equivalent local contract files first when present',
    '- use local files and inspection tools directly when needed, but stay read-only',
    '- do not edit files, write patches, commit, or run destructive commands',
    '- avoid long builds or test suites unless a supplied context file explicitly calls for one precise check',
    '- keep evidence compact and path-backed; prefer file paths and direct observations over broad opinion',
    '- if evidence is missing, say so explicitly instead of guessing',
    ...phaseSpecificRules,
    '',
    'Viewpoint focus:',
    ...focus.map((line) => `- ${line}`),
    '',
    'Working goal:',
    options.goal,
    '',
    contextBlock,
    extraInstructions,
    '',
    'Return JSON only. Do not wrap it in Markdown fences. Use this exact shape:',
    ...returnShape,
    '',
    'If you have no substantial findings, return an empty findings array and explain that in summary.',
  ].join('\n')
}

async function runChild(command, args, options) {
  const stdoutChunks = []
  const stderrChunks = []

  return await new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      shell: false,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
      },
    })

    const timeout = setTimeout(() => {
      child.kill()
      reject(new Error(`Claude invocation timed out after ${options.timeoutMs}ms`))
    }, options.timeoutMs)

    child.stdout.on('data', (chunk) => {
      stdoutChunks.push(Buffer.from(chunk))
    })

    child.stderr.on('data', (chunk) => {
      stderrChunks.push(Buffer.from(chunk))
    })

    if (typeof options.stdinText === 'string') {
      child.stdin.write(options.stdinText, 'utf8')
    }
    child.stdin.end()

    child.on('error', (error) => {
      clearTimeout(timeout)
      reject(error)
    })

    child.on('close', (code) => {
      clearTimeout(timeout)
      resolve({
        code: code ?? 1,
        stdout: Buffer.concat(stdoutChunks).toString('utf8'),
        stderr: Buffer.concat(stderrChunks).toString('utf8'),
      })
    })
  })
}

async function runClaudeLane(options, viewpoint, paths, extraDirs) {
  const prompt = buildPrompt(options, viewpoint, options.contextFiles)
  await fs.writeFile(paths.promptPath, prompt, 'utf8')

  if (options.dryRun) {
    return {
      status: 'dry_run',
      prompt,
    }
  }

  const claudeArgs = buildClaudeArgs(options, viewpoint, extraDirs)

  let result
  if (process.platform === 'win32') {
    const psCommand = [
      '[Console]::InputEncoding = [System.Text.Encoding]::UTF8',
      '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8',
      '$OutputEncoding = [System.Text.Encoding]::UTF8',
      `$claudeArgs = @(${claudeArgs.map((arg) => quotePowerShell(arg)).join(', ')})`,
      `Get-Content -Raw -Encoding UTF8 -LiteralPath ${quotePowerShell(paths.promptPath)} | claude @claudeArgs`,
      'exit $LASTEXITCODE',
    ].join('; ')

    result = await runChild('powershell', ['-NoProfile', '-Command', psCommand], {
      cwd: options.workspace,
      timeoutMs: options.timeoutMs,
    })
  } else {
    result = await runChild('claude', [...claudeArgs], {
      cwd: options.workspace,
      timeoutMs: options.timeoutMs,
      stdinText: prompt,
    })
  }

  await fs.writeFile(paths.responsePath, result.stdout, 'utf8')
  if (result.stderr.trim()) {
    await fs.writeFile(paths.stderrPath, result.stderr, 'utf8')
  }

  if (result.code !== 0) {
    throw new Error(`Claude lane exited with code ${result.code}${result.stderr ? `\n${result.stderr}` : ''}`)
  }

  const parsed = JSON.parse(extractJsonCandidate(result.stdout))
  const normalized = normalizeLanePayload(parsed, viewpoint, options.phase)
  await fs.writeFile(paths.parsedPath, `${JSON.stringify(normalized, null, 2)}\n`, 'utf8')

  return {
    status: 'completed',
    prompt,
    raw: result.stdout,
    parsed: normalized,
  }
}

function buildLanePaths(outDir, viewpoint, index) {
  const prefix = `${String(index + 1).padStart(2, '0')}-${viewpoint}`
  return {
    promptPath: join(outDir, `${prefix}.prompt.md`),
    responsePath: join(outDir, `${prefix}.response.txt`),
    stderrPath: join(outDir, `${prefix}.stderr.txt`),
    parsedPath: join(outDir, `${prefix}.json`),
  }
}

function buildMarkdownSummary(manifest) {
  const lines = [
    '# Claude Research Lanes',
    '',
    `- Workspace: ${manifest.workspace}`,
    `- Phase: ${manifest.phase}`,
    `- Model: ${manifest.model}`,
    `- Effort: ${manifest.effort}`,
    `- Viewpoint Profile: ${manifest.viewpointProfile}`,
    `- Generated At: ${manifest.generatedAt}`,
    `- Dry Run: ${manifest.dryRun ? 'yes' : 'no'}`,
    '',
    '## Goal',
    '',
    manifest.goal,
    '',
  ]

  if (manifest.contextFiles.length > 0) {
    lines.push('## Context Files', '')
    for (const filePath of manifest.contextFiles) {
      lines.push(`- ${filePath}`)
    }
    lines.push('')
  }

  for (const lane of manifest.lanes) {
    lines.push(`## ${lane.viewpoint}`, '')
    lines.push(`- Status: ${lane.status}`)

    if (lane.error) {
      lines.push(`- Error: ${lane.error}`, '')
      continue
    }

    if (lane.status === 'dry_run') {
      lines.push(`- Prompt: ${lane.promptPath}`, '')
      continue
    }

    lines.push(`- Confidence: ${lane.parsed.confidence}`)
    lines.push(`- Summary: ${lane.parsed.summary || '(empty)'}`)
    lines.push(`- Parsed JSON: ${lane.parsedPath}`)

    if (lane.parsed.autonomous_halt_permission) {
      lines.push(`- Autonomous Halt Permission: ${lane.parsed.autonomous_halt_permission.decision}`)
      if (lane.parsed.autonomous_halt_permission.reason) {
        lines.push(`- Halt Reason: ${lane.parsed.autonomous_halt_permission.reason}`)
      }
      if (lane.parsed.autonomous_halt_permission.blocking_conditions.length > 0) {
        lines.push('- Halt Blocking Conditions:')
        for (const item of lane.parsed.autonomous_halt_permission.blocking_conditions) {
          lines.push(`  - ${item}`)
        }
      }
      if (lane.parsed.autonomous_halt_permission.required_evidence.length > 0) {
        lines.push('- Halt Required Evidence:')
        for (const item of lane.parsed.autonomous_halt_permission.required_evidence) {
          lines.push(`  - ${item}`)
        }
      }
    }

    if (lane.parsed.findings.length === 0) {
      lines.push('- Findings: none')
    } else {
      lines.push('- Findings:')
      for (const finding of lane.parsed.findings) {
        lines.push(`  - [${finding.severity}] ${finding.title || '(untitled)'}`)
        if (finding.detail) {
          lines.push(`    - ${finding.detail}`)
        }
        if (finding.plan_implication) {
          lines.push(`    - implication: ${finding.plan_implication}`)
        }
        for (const evidence of finding.evidence) {
          lines.push(`    - evidence: ${evidence}`)
        }
      }
    }

    if (lane.parsed.recommended_stage_shape.length > 0) {
      lines.push('- Recommended Stage Shape:')
      for (const item of lane.parsed.recommended_stage_shape) {
        lines.push(`  - ${item}`)
      }
    }

    if (lane.parsed.open_questions.length > 0) {
      lines.push('- Open Questions:')
      for (const item of lane.parsed.open_questions) {
        lines.push(`  - ${item}`)
      }
    }

    lines.push('')
  }

  return `${lines.join('\n')}\n`
}

async function main() {
  const options = parseArgs(process.argv.slice(2))

  if (!options.workspace) {
    throw new Error('--workspace is required')
  }

  options.workspace = resolve(options.workspace)
  if (!existsSync(options.workspace)) {
    throw new Error(`Workspace does not exist: ${options.workspace}`)
  }

  if (options.goalFile) {
    const goalFile = resolve(options.goalFile)
    if (!existsSync(goalFile)) {
      throw new Error(`Goal file does not exist: ${goalFile}`)
    }
    options.goal = (await fs.readFile(goalFile, 'utf8')).trim()
  }

  if (!options.goal?.trim()) {
    throw new Error('Either --goal or --goal-file must provide non-empty goal text')
  }
  options.goal = options.goal.trim()
  if (options.phase === 'stop_authorization') {
    options.viewpointProfile = 'extended'
  }
  options.viewpoints = VIEWPOINT_PROFILES[options.viewpointProfile]

  options.contextFiles = options.contextFiles.map((filePath) => resolve(filePath))
  for (const contextFile of options.contextFiles) {
    if (!existsSync(contextFile)) {
      throw new Error(`Context file does not exist: ${contextFile}`)
    }
  }

  const defaultOutDir = join(
    options.workspace,
    '.agents',
    'agent-loop',
    'claude-research',
    `${options.phase}-${timestampId()}`,
  )
  options.outDir = resolve(options.outDir || defaultOutDir)
  await fs.mkdir(options.outDir, { recursive: true })

  const extraDirs = [...new Set(
    options.contextFiles
      .map((filePath) => dirname(filePath))
      .filter((dirPath) => resolve(dirPath) !== options.workspace),
  )]

  const laneResults = await Promise.allSettled(
    options.viewpoints.map(async (viewpoint, index) => {
      const paths = buildLanePaths(options.outDir, viewpoint, index)
      const laneResult = await runClaudeLane(options, viewpoint, paths, extraDirs)
      return {
        viewpoint,
        ...paths,
        ...laneResult,
      }
    }),
  )

  const lanes = laneResults.map((result, index) => {
    const viewpoint = options.viewpoints[index]
    const paths = buildLanePaths(options.outDir, viewpoint, index)

    if (result.status === 'fulfilled') {
      const value = result.value
      return {
        viewpoint,
        status: value.status,
        promptPath: value.promptPath,
        responsePath: value.responsePath,
        stderrPath: value.stderrPath,
        parsedPath: value.parsedPath,
        parsed: value.parsed,
      }
    }

    return {
      viewpoint,
      status: 'failed',
      promptPath: paths.promptPath,
      responsePath: paths.responsePath,
      stderrPath: paths.stderrPath,
      parsedPath: paths.parsedPath,
      error: result.reason instanceof Error ? result.reason.message : String(result.reason),
    }
  })

  const manifest = {
    workspace: options.workspace,
    phase: options.phase,
    model: options.model,
    effort: options.effort,
    viewpointProfile: options.viewpointProfile,
    goal: options.goal,
    contextFiles: options.contextFiles,
    generatedAt: new Date().toISOString(),
    dryRun: options.dryRun,
    bypassPermissions: options.bypassPermissions,
    lanes,
  }

  const manifestPath = join(options.outDir, 'research-lanes.json')
  const summaryPath = join(options.outDir, 'research-lanes.md')
  await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8')
  await fs.writeFile(summaryPath, buildMarkdownSummary(manifest), 'utf8')

  console.log(`Claude research lanes manifest: ${manifestPath}`)
  console.log(`Claude research lanes summary: ${summaryPath}`)

  const failedCount = lanes.filter((lane) => lane.status === 'failed').length
  if (failedCount > 0) {
    process.exitCode = 1
  }
}

void main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  usage()
  process.exit(1)
})
