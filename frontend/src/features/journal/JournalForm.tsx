import { FormEvent, useState } from 'react'
import { journalApi } from '../../services/journalApi'
import type { JournalCreatePayload } from '../../types/api'
import { TagInput } from './TagInput'

type JournalFormProps = {
  tradeId?: string
  onCreated: () => void
}

export function JournalForm({ tradeId, onCreated }: JournalFormProps) {
  const [entryReason, setEntryReason] = useState('')
  const [exitReason, setExitReason] = useState('')
  const [notes, setNotes] = useState('')
  const [lessonsLearned, setLessonsLearned] = useState('')
  const [riskScore, setRiskScore] = useState('')
  const [tags, setTags] = useState<string[]>([])
  const [screenshotUrl, setScreenshotUrl] = useState('')
  const [screenshotUrls, setScreenshotUrls] = useState<string[]>([])
  const [message, setMessage] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    if (!tradeId || !entryReason || !exitReason) {
      setMessage('Trade ID, entry reason, and exit reason are required.')
      return
    }

    const payload: JournalCreatePayload = {
      trade_id: tradeId,
      entry_reason: entryReason,
      exit_reason: exitReason,
      notes: notes || null,
      lessons_learned: lessonsLearned || null,
      risk_score: riskScore ? Number(riskScore) : null,
      tag_names: tags,
      screenshot_urls: screenshotUrls
    }

    try {
      await journalApi.create(payload)
      setEntryReason('')
      setExitReason('')
      setNotes('')
      setLessonsLearned('')
      setRiskScore('')
      setTags([])
      setScreenshotUrl('')
      setScreenshotUrls([])
      setMessage('Journal entry created.')
      onCreated()
    } catch {
      setMessage('Unable to create journal entry.')
    }
  }

  function addScreenshot() {
    if (!screenshotUrl.trim() || screenshotUrls.includes(screenshotUrl.trim())) {
      return
    }
    setScreenshotUrls([...screenshotUrls, screenshotUrl.trim()])
    setScreenshotUrl('')
  }

  return (
    <form onSubmit={submit} className="card space-y-4">
      <h2 className="text-xl font-bold text-slate-100">New Journal Entry</h2>
      <input className="input" value={tradeId ?? ''} disabled placeholder="Trade ID" />
      <textarea className="input min-h-24" value={entryReason} onChange={(event) => setEntryReason(event.target.value)} placeholder="Entry reason" />
      <textarea className="input min-h-24" value={exitReason} onChange={(event) => setExitReason(event.target.value)} placeholder="Exit reason" />
      <textarea className="input min-h-24" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Notes" />
      <textarea className="input min-h-24" value={lessonsLearned} onChange={(event) => setLessonsLearned(event.target.value)} placeholder="Lessons learned" />
      <input className="input" type="number" min={1} max={10} value={riskScore} onChange={(event) => setRiskScore(event.target.value)} placeholder="Risk score 1-10" />
      <TagInput value={tags} onChange={setTags} />
      <div className="flex gap-2">
        <input className="input flex-1" value={screenshotUrl} onChange={(event) => setScreenshotUrl(event.target.value)} placeholder="Screenshot URL" />
        <button className="btn" type="button" onClick={addScreenshot}>Add screenshot</button>
      </div>
      {screenshotUrls.length > 0 && <p className="text-sm text-slate-400">{screenshotUrls.length} screenshot URL(s) queued</p>}
      <button className="btn w-full" type="submit">Save Journal</button>
      {message && <p className="text-sm text-cyan-300">{message}</p>}
    </form>
  )
}
