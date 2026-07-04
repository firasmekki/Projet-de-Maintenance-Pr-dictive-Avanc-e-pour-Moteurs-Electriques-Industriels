import { useState } from 'react'
import { Settings, ChevronDown, ChevronUp } from 'lucide-react'
import type { MotorProfile } from '../types'

interface Props {
  onChange: (profile: MotorProfile | null) => void
}

const MANUFACTURERS = ['Siemens', 'ABB', 'Schneider Electric', 'WEG', 'SEW-Eurodrive', 'Leroy-Somer', 'Nidec', 'Toshiba', 'Autre']
const INS_CLASSES   = ['A (105°C)', 'B (130°C)', 'F (155°C)', 'H (180°C)']
const EFF_CLASSES   = ['IE1', 'IE2', 'IE3', 'IE4']
const PROT_CLASSES  = ['IP44', 'IP54', 'IP55', 'IP65', 'IP66']

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-gray-600 dark:text-slate-400 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  )
}

const inputCls = `w-full px-3 py-2 text-sm rounded-lg
  bg-gray-50 border border-gray-200 text-gray-900 placeholder-gray-400
  focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/20
  dark:bg-slate-700/50 dark:border-slate-600 dark:text-slate-200 dark:placeholder-slate-500`

export default function MotorProfileForm({ onChange }: Props) {
  const [open,    setOpen]    = useState(false)
  const [profile, setProfile] = useState<MotorProfile>({})

  const update = (key: keyof MotorProfile, value: string | number | undefined) => {
    const updated = { ...profile, [key]: value === '' ? undefined : value }
    setProfile(updated)
    const hasData = Object.values(updated).some(v => v !== undefined && v !== '')
    onChange(hasData ? updated : null)
  }

  return (
    <div className="card">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center gap-2 text-left"
      >
        <Settings className="w-4 h-4 text-blue-500" />
        <span className="font-semibold text-gray-800 dark:text-slate-200">
          Profil Moteur
          <span className="ml-2 text-xs font-normal text-gray-500 dark:text-slate-400">(optionnel — améliore la précision du diagnostic)</span>
        </span>
        {open
          ? <ChevronUp   className="w-4 h-4 text-gray-400 ml-auto" />
          : <ChevronDown className="w-4 h-4 text-gray-400 ml-auto" />
        }
      </button>

      {open && (
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Field label="Nom / ID Moteur">
            <input className={inputCls} placeholder="ex: MTR-01, Pompe P-12..."
              value={profile.name ?? ''} onChange={e => update('name', e.target.value)} />
          </Field>

          <Field label="Fabricant">
            <select className={inputCls} value={profile.manufacturer ?? ''}
              onChange={e => update('manufacturer', e.target.value)}>
              <option value="">— Sélectionner —</option>
              {MANUFACTURERS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </Field>

          <Field label="Puissance nominale (kW)">
            <input type="number" min="0" step="0.1" className={inputCls} placeholder="ex: 22"
              value={profile.nominal_power_kw ?? ''}
              onChange={e => update('nominal_power_kw', e.target.value ? Number(e.target.value) : undefined)} />
          </Field>

          <Field label="Tension nominale (V)">
            <input type="number" min="0" className={inputCls} placeholder="ex: 400"
              value={profile.nominal_voltage_v ?? ''}
              onChange={e => update('nominal_voltage_v', e.target.value ? Number(e.target.value) : undefined)} />
          </Field>

          <Field label="★ Courant nominal (A)">
            <input type="number" min="0" step="0.1" className={`${inputCls} border-blue-300 dark:border-blue-700`}
              placeholder="ex: 45 — améliore la détection surcharge"
              value={profile.nominal_current_a ?? ''}
              onChange={e => update('nominal_current_a', e.target.value ? Number(e.target.value) : undefined)} />
          </Field>

          <Field label="Vitesse nominale (tr/min)">
            <input type="number" min="0" className={inputCls} placeholder="ex: 1450, 2900"
              value={profile.nominal_speed_rpm ?? ''}
              onChange={e => update('nominal_speed_rpm', e.target.value ? Number(e.target.value) : undefined)} />
          </Field>

          <Field label="Classe d'isolation">
            <select className={inputCls} value={profile.insulation_class ?? ''}
              onChange={e => update('insulation_class', e.target.value)}>
              <option value="">— Sélectionner —</option>
              {INS_CLASSES.map(c => <option key={c} value={c.split(' ')[0]}>{c}</option>)}
            </select>
          </Field>

          <Field label="Classe d'efficacité">
            <select className={inputCls} value={profile.efficiency_class ?? ''}
              onChange={e => update('efficiency_class', e.target.value)}>
              <option value="">— Sélectionner —</option>
              {EFF_CLASSES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>

          <Field label="Indice de protection">
            <select className={inputCls} value={profile.protection_class ?? ''}
              onChange={e => update('protection_class', e.target.value)}>
              <option value="">— Sélectionner —</option>
              {PROT_CLASSES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
        </div>
      )}

      {open && (
        <p className="mt-3 text-xs text-blue-600 dark:text-blue-400">
          ★ Le courant nominal est le paramètre le plus important — il permet de calculer le ratio de surcharge avec précision.
        </p>
      )}
    </div>
  )
}
