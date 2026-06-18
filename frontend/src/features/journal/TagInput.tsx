import { FormEvent, KeyboardEvent, useState } from 'react'

type TagInputProps = {
  value: string[]
  onChange: (tags: string[]) => void
  placeholder?: string
}

export function TagInput({ value, onChange, placeholder = 'Add tag and press Enter' }: TagInputProps) {
  const [draft, setDraft] = useState('')

  function addTag(tag: string) {
    const normalized = tag.trim()
    if (!normalized || value.includes(normalized)) {
      return
    }
    onChange([...value, normalized])
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    addTag(draft)
    setDraft('')
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      addTag(draft)
      setDraft('')
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2">
        {value.map((tag) => (
          <button
            key={tag}
            type="button"
            className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm text-cyan-200 hover:bg-cyan-500/20"
            onClick={() => onChange(value.filter((item) => item !== tag))}
          >
            {tag} ×
          </button>
        ))}
      </div>
      <form onSubmit={submit}>
        <input className="input" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={handleKeyDown} placeholder={placeholder} />
      </form>
    </div>
  )
}
