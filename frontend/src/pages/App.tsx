import { useEffect, useState } from 'react'
import { apiGet, apiPatch, getTelegramUser } from '../api/client'

interface ScheduleEntry {
  id: number
  date: string
  time_start: string
  time_end: string
  description: string
  location: string
}

interface ChecklistItem {
  id: number
  text: string
  is_done: boolean
  order: number
}

interface Checklist {
  id: number
  title: string
  is_completed: boolean
  created_at: string
  items: ChecklistItem[]
}

export default function App() {
  const [tab, setTab] = useState<'schedule' | 'checklists'>('schedule')
  const [schedule, setSchedule] = useState<ScheduleEntry[]>([])
  const [checklists, setChecklists] = useState<Checklist[]>([])
  const [loading, setLoading] = useState(true)

  const user = getTelegramUser()

  useEffect(() => {
    window.Telegram?.WebApp?.ready()
    window.Telegram?.WebApp?.expand()
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [s, c] = await Promise.all([
        apiGet<ScheduleEntry[]>('/schedule/my'),
        apiGet<Checklist[]>('/checklists/my'),
      ])
      setSchedule(s)
      setChecklists(c)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function toggleItem(checklistId: number, itemId: number, currentDone: boolean) {
    await apiPatch(`/checklists/items/${itemId}`, { is_done: !currentDone })
    setChecklists(prev =>
      prev.map(cl =>
        cl.id === checklistId
          ? {
              ...cl,
              items: cl.items.map(it =>
                it.id === itemId ? { ...it, is_done: !currentDone } : it
              ),
            }
          : cl
      )
    )
  }

  const groupedSchedule = schedule.reduce((acc, entry) => {
    const key = entry.date || 'Без дати'
    if (!acc[key]) acc[key] = []
    acc[key].push(entry)
    return acc
  }, {} as Record<string, ScheduleEntry[]>)

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Завантаження...</div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <h1>5Stars Alarm</h1>
        {user && <p>Привіт, {user.first_name}!</p>}
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'schedule' ? 'active' : ''}`} onClick={() => setTab('schedule')}>
          📅 Розклад
        </button>
        <button className={`tab ${tab === 'checklists' ? 'active' : ''}`} onClick={() => setTab('checklists')}>
          ✅ Чеклісти
          {checklists.some(cl => cl.items.some(it => !it.is_done)) && (
            <span style={{ marginLeft: 6, background: '#e53935', borderRadius: '50%', width: 8, height: 8, display: 'inline-block' }} />
          )}
        </button>
      </div>

      {tab === 'schedule' && (
        <div>
          {Object.keys(groupedSchedule).length === 0 ? (
            <div className="empty">📅 Розклад поки порожній</div>
          ) : (
            Object.entries(groupedSchedule).map(([date, entries]) => (
              <div key={date}>
                <div className="label" style={{ marginBottom: 8 }}>{date}</div>
                {entries.map(e => (
                  <div className="card" key={e.id}>
                    <div className="card-title">{e.description || 'Подія'}</div>
                    <div className="card-meta">
                      {e.time_start && `🕐 ${e.time_start}${e.time_end ? ` – ${e.time_end}` : ''}`}
                      {e.location && ` · 📍 ${e.location}`}
                    </div>
                  </div>
                ))}
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'checklists' && (
        <div>
          {checklists.length === 0 ? (
            <div className="empty">✅ Чеклістів поки немає</div>
          ) : (
            checklists.map(cl => {
              const done = cl.items.filter(i => i.is_done).length
              const total = cl.items.length
              return (
                <div className="card" key={cl.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div className="card-title">{cl.title}</div>
                    <span className={`badge ${done === total && total > 0 ? 'badge-green' : 'badge-orange'}`}>
                      {done}/{total}
                    </span>
                  </div>
                  {cl.items.map(item => (
                    <div className="checklist-item" key={item.id}>
                      <input
                        type="checkbox"
                        id={`item-${item.id}`}
                        checked={item.is_done}
                        onChange={() => toggleItem(cl.id, item.id, item.is_done)}
                      />
                      <label htmlFor={`item-${item.id}`} className={item.is_done ? 'done' : ''}>
                        {item.text}
                      </label>
                    </div>
                  ))}
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
