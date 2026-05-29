import { useEffect, useState } from 'react'
import { apiGet, apiPost, apiUpload, apiDelete } from '../api/client'

interface Person {
  id: number
  name: string
  telegram_user_id: number | null
  telegram_username: string | null
}

interface ChecklistItem {
  id: number
  text: string
  is_done: boolean
}

interface Checklist {
  id: number
  title: string
  person_id: number | null
  items: ChecklistItem[]
}

interface Alert {
  id: number
  person_id: number
  message: string
  send_at: string | null
  is_sent: boolean
  is_active: boolean
  repeat_daily: boolean
}

type Tab = 'persons' | 'checklists' | 'alerts' | 'notify'

export default function Admin() {
  const [tab, setTab] = useState<Tab>('persons')
  const [persons, setPersons] = useState<Person[]>([])
  const [checklists, setChecklists] = useState<Checklist[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [uploadMsg, setUploadMsg] = useState('')

  const [assignPersonId, setAssignPersonId] = useState('')
  const [assignTgId, setAssignTgId] = useState('')
  const [assignTgUsername, setAssignTgUsername] = useState('')

  const [clTitle, setClTitle] = useState('')
  const [clPersonId, setClPersonId] = useState('')
  const [clItems, setClItems] = useState('')

  const [alertPersonId, setAlertPersonId] = useState('')
  const [alertMsg, setAlertMsg] = useState('')
  const [alertSendAt, setAlertSendAt] = useState('')
  const [alertRepeat, setAlertRepeat] = useState(false)

  const [notifyMsg, setNotifyMsg] = useState('')
  const [newAdminId, setNewAdminId] = useState('')

  useEffect(() => {
    window.Telegram?.WebApp?.ready()
    window.Telegram?.WebApp?.expand()
    loadAll()
  }, [])

  async function loadAll() {
    setLoading(true)
    try {
      const [p, c, a] = await Promise.all([
        apiGet<Person[]>('/admin/persons'),
        apiGet<Checklist[]>('/checklists'),
        apiGet<Alert[]>('/alerts'),
      ])
      setPersons(p)
      setChecklists(c)
      setAlerts(a)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadMsg('Завантаження...')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await apiUpload<{ message: string; persons: Person[] }>('/admin/upload-schedule', fd)
      setUploadMsg(res.message)
      setPersons(res.persons)
    } catch (err: unknown) {
      setUploadMsg('Помилка: ' + (err instanceof Error ? err.message : String(err)))
    }
    e.target.value = ''
  }

  async function handleAssignPerson() {
    if (!assignPersonId) return
    await apiPost('/admin/assign-person', {
      person_id: parseInt(assignPersonId),
      telegram_user_id: assignTgId ? parseInt(assignTgId) : undefined,
      telegram_username: assignTgUsername || undefined,
    })
    setAssignPersonId(''); setAssignTgId(''); setAssignTgUsername('')
    await loadAll()
  }

  async function handleCreateChecklist() {
    if (!clTitle.trim()) return
    const items = clItems.split('\n').filter(s => s.trim()).map((text, i) => ({ text: text.trim(), order: i }))
    await apiPost('/checklists', {
      title: clTitle,
      person_id: clPersonId ? parseInt(clPersonId) : undefined,
      items,
    })
    setClTitle(''); setClPersonId(''); setClItems('')
    await loadAll()
  }

  async function handleCreateAlert() {
    if (!alertPersonId || !alertMsg.trim()) return
    await apiPost('/alerts', {
      person_id: parseInt(alertPersonId),
      message: alertMsg,
      send_at: alertSendAt || undefined,
      repeat_daily: alertRepeat,
    })
    setAlertPersonId(''); setAlertMsg(''); setAlertSendAt(''); setAlertRepeat(false)
    await loadAll()
  }

  async function handleAssignAdmin() {
    if (!newAdminId) return
    await apiPost('/admin/assign-admin', { telegram_user_id: parseInt(newAdminId) })
    setNewAdminId('')
    alert(`Призначено адміна: ${newAdminId}`)
  }

  async function handleDeleteChecklist(id: number) {
    if (!confirm('Видалити чеклист?')) return
    await apiDelete(`/checklists/${id}`)
    await loadAll()
  }

  async function handleDeleteAlert(id: number) {
    await apiDelete(`/alerts/${id}`)
    await loadAll()
  }

  if (loading) {
    return <div className="container"><div className="loading">Завантаження...</div></div>
  }

  return (
    <div className="container">
      <div className="header">
        <h1>⚙️ Адмін-панель</h1>
        <p>5Stars Alarm</p>
      </div>

      <div className="tabs">
        {(['persons', 'checklists', 'alerts', 'notify'] as Tab[]).map(t => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t === 'persons' ? '👥 Люди' : t === 'checklists' ? '✅ Чеклісти' : t === 'alerts' ? '🔔 Алерти' : '📢 Сповіщення'}
          </button>
        ))}
      </div>

      {tab === 'persons' && (
        <div>
          <div className="section-title">Завантажити розклад</div>
          <div className="card">
            <p style={{ fontSize: 13, marginBottom: 10, color: 'var(--tg-theme-hint-color)' }}>
              Excel або CSV з колонками: name, date, time_start, time_end, description, location
            </p>
            <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload}
              style={{ fontSize: 13, marginBottom: 8, width: '100%' }} />
            {uploadMsg && <p style={{ fontSize: 13, color: '#43a047' }}>{uploadMsg}</p>}
          </div>

          <div className="section-title" style={{ marginTop: 16 }}>Призначити Telegram</div>
          <div className="card">
            <div className="form-group">
              <div className="label">Людина</div>
              <select className="select" value={assignPersonId} onChange={e => setAssignPersonId(e.target.value)}>
                <option value="">— оберіть —</option>
                {persons.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <div className="label">Telegram ID</div>
              <input className="input" placeholder="123456789" value={assignTgId} onChange={e => setAssignTgId(e.target.value)} />
            </div>
            <div className="form-group">
              <div className="label">або Username</div>
              <input className="input" placeholder="@username" value={assignTgUsername} onChange={e => setAssignTgUsername(e.target.value)} />
            </div>
            <button className="btn" onClick={handleAssignPerson}>Призначити</button>
          </div>

          <div className="section-title" style={{ marginTop: 16 }}>Всі люди</div>
          {persons.map(p => (
            <div className="card" key={p.id}>
              <div className="card-title">{p.name}</div>
              <div className="card-meta">
                {p.telegram_user_id ? `ID: ${p.telegram_user_id}` : ''}
                {p.telegram_username ? ` · @${p.telegram_username}` : ''}
                {!p.telegram_user_id && !p.telegram_username && 'Не прив\'язаний'}
              </div>
            </div>
          ))}

          <div className="section-title" style={{ marginTop: 16 }}>Призначити нового адміна</div>
          <div className="card">
            <input className="input" placeholder="Telegram ID" value={newAdminId} onChange={e => setNewAdminId(e.target.value)} />
            <button className="btn" onClick={handleAssignAdmin}>Зробити адміном</button>
          </div>
        </div>
      )}

      {tab === 'checklists' && (
        <div>
          <div className="section-title">Новий чеклист</div>
          <div className="card">
            <div className="form-group">
              <div className="label">Назва</div>
              <input className="input" placeholder="Назва чеклісту" value={clTitle} onChange={e => setClTitle(e.target.value)} />
            </div>
            <div className="form-group">
              <div className="label">Призначити людині</div>
              <select className="select" value={clPersonId} onChange={e => setClPersonId(e.target.value)}>
                <option value="">— всі —</option>
                {persons.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <div className="label">Пункти (кожен з нового рядка)</div>
              <textarea className="input" rows={5} placeholder={"Завдання 1\nЗавдання 2\nЗавдання 3"}
                value={clItems} onChange={e => setClItems(e.target.value)} style={{ resize: 'vertical' }} />
            </div>
            <button className="btn" onClick={handleCreateChecklist}>Створити чеклист</button>
          </div>

          <div className="section-title" style={{ marginTop: 16 }}>Всі чеклісти</div>
          {checklists.map(cl => {
            const person = persons.find(p => p.id === cl.person_id)
            return (
              <div className="card" key={cl.id}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div className="card-title">{cl.title}</div>
                  <button className="btn btn-danger" style={{ width: 'auto', padding: '4px 10px', margin: 0, fontSize: 12 }}
                    onClick={() => handleDeleteChecklist(cl.id)}>✕</button>
                </div>
                {person && <div className="card-meta">👤 {person.name}</div>}
                {cl.items.map(i => (
                  <div key={i.id} style={{ fontSize: 13, padding: '3px 0', color: i.is_done ? 'var(--tg-theme-hint-color)' : 'inherit' }}>
                    {i.is_done ? '✅' : '⬜'} {i.text}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}

      {tab === 'alerts' && (
        <div>
          <div className="section-title">Новий алерт</div>
          <div className="card">
            <div className="form-group">
              <div className="label">Людина</div>
              <select className="select" value={alertPersonId} onChange={e => setAlertPersonId(e.target.value)}>
                <option value="">— оберіть —</option>
                {persons.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <div className="label">Повідомлення</div>
              <textarea className="input" rows={3} placeholder="Текст сповіщення..."
                value={alertMsg} onChange={e => setAlertMsg(e.target.value)} style={{ resize: 'vertical' }} />
            </div>
            <div className="form-group">
              <div className="label">Час надсилання (необов'язково)</div>
              <input className="input" type="datetime-local" value={alertSendAt} onChange={e => setAlertSendAt(e.target.value)} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <input type="checkbox" id="repeat" checked={alertRepeat} onChange={e => setAlertRepeat(e.target.checked)} />
              <label htmlFor="repeat" style={{ fontSize: 14 }}>Повторювати щодня</label>
            </div>
            <button className="btn" onClick={handleCreateAlert}>Створити алерт</button>
          </div>

          <div className="section-title" style={{ marginTop: 16 }}>Активні алерти</div>
          {alerts.filter(a => a.is_active).map(a => {
            const person = persons.find(p => p.id === a.person_id)
            return (
              <div className="card" key={a.id}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div className="card-title">{a.message}</div>
                  <button className="btn btn-danger" style={{ width: 'auto', padding: '4px 10px', margin: 0, fontSize: 12 }}
                    onClick={() => handleDeleteAlert(a.id)}>✕</button>
                </div>
                <div className="card-meta">
                  {person && `👤 ${person.name} · `}
                  {a.send_at ? `🕐 ${new Date(a.send_at).toLocaleString('uk-UA')}` : 'Одразу'}
                  {a.repeat_daily && ' · 🔄 щодня'}
                  {a.is_sent && ' · ✅ надіслано'}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {tab === 'notify' && (
        <div>
          <div className="section-title">Масове сповіщення</div>
          <div className="card">
            <p style={{ fontSize: 13, marginBottom: 10, color: 'var(--tg-theme-hint-color)' }}>
              Надіслати повідомлення всім зареєстрованим користувачам.
            </p>
            <textarea className="input" rows={4} placeholder="Текст повідомлення..."
              value={notifyMsg} onChange={e => setNotifyMsg(e.target.value)} style={{ resize: 'vertical' }} />
            <button className="btn" onClick={async () => {
              if (!notifyMsg.trim()) return
              try {
                const res = await apiPost<{ sent: number }>('/notifications/broadcast', { message: notifyMsg })
                alert(`Надіслано: ${'sent' in res ? res.sent : 0} користувачів`)
                setNotifyMsg('')
              } catch (e) {
                alert('Помилка: ' + String(e))
              }
            }}>📢 Надіслати всім</button>
          </div>
        </div>
      )}
    </div>
  )
}
