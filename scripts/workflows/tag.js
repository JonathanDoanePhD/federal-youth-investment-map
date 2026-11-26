export const meta = {
  name: 'federal-youth-investment-tag',
  description: 'Tag NSF youth STEM awards and OJJDP mentoring grants per protocol, writing validated JSON to disk',
  phases: [{ title: 'Tag', detail: 'one agent per batch' }],
}
const ROOT = '/home/user/claude_projects/projects/09-federal-youth-investment-map'
const SCHEMA = {
  type: 'object',
  properties: { batch: { type: 'string' }, n_records: { type: 'integer' }, valid: { type: 'boolean' }, issues: { type: 'string' } },
  required: ['batch', 'n_records', 'valid', 'issues'],
}
// args: {jobs: [{kind: 'nsf'|'ojjdp', pass: 'main'|'reference', batch: 'batch_0001', model?: 'sonnet'}]}
const outPath = (j) => j.kind === 'nsf' ? `${ROOT}/data/coded/nsf/${j.pass}/${j.batch}.json` : `${ROOT}/data/coded/ojjdp/${j.batch}.json`
const prompt = (j) => {
  const part = j.kind === 'nsf' ? 'Part A: NSF award tagging' : 'Part B: OJJDP mentoring grant tagging'
  const keys = j.kind === 'nsf'
    ? 'id, serves_youth, audience, grade_band, models, mentoring, bridging, ai_cs, targets, setting, youth_reach, evaluation, service_geography, notes'
    : 'id, org_scope, targets, format, purpose, notes'
  const other = j.kind === 'nsf' ? `\nAnother tagger codes some batches independently: do NOT open anything under ${ROOT}/data/coded/nsf/ except your own output file.` : ''
  return `You are tagging federal grant records for a research map of youth STEM and mentoring investment.${other}

1. Read ${ROOT}/docs/protocol.md, section "${part}". Follow it exactly; tag only what the record states.
2. Read the input batch ${ROOT}/data/interim/batches/${j.kind}/${j.batch}.jsonl (one JSON record per line).${j.kind === 'nsf' ? ' Read EVERY abstract IN FULL (print long abstracts in chunks); key details such as youth served, mentoring and evaluation design are often near the end.' : ''}
3. For every record produce one object with exactly these keys: ${keys}. "id" is the record's id as a string. notes: your own words, within the protocol's word limit.
4. Write the JSON list to ${outPath(j)} (create folders if needed; a short Python script is fine).
5. Run: python3 -I ${ROOT}/scripts/validate.py ${j.kind} ${outPath(j)} and fix until it prints VALID.
6. Keep ALL temporary files in your PRIVATE folder ${ROOT}/data/interim/tmp/${j.kind}_${j.pass || 'main'}_${j.batch}/ (create it). Never use the shared scratchpad or /tmp: other agents run at the same time. Build the output by matching each record's id, never by position. Do not modify any other files. Do not run git.
Return counts from your final file; valid=true only if the validator printed VALID. In "issues", confirm you read every record in full and note hard calls briefly.`
}
log(`Tagging ${args.jobs.length} batch(es)`)
const results = await parallel(args.jobs.map(j => () =>
  agent(prompt(j), { label: `${j.kind} ${j.pass || ''} ${j.batch}`, phase: 'Tag', schema: SCHEMA, ...(j.model ? { model: j.model } : {}) })))
const ok = results.filter(Boolean)
log(`Done: ${ok.filter(r => r.valid).length}/${args.jobs.length} valid`)
return ok
