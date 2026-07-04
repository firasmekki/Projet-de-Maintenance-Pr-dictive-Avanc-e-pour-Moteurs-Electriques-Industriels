export interface UploadResponse {
  report_id:      string
  filename:       string
  file_size:      number
  row_count:      number
  column_count:   number
  missing_values: number
  quality_score:  number
  columns:        string[]
  preview:        Record<string, unknown>[]
  status:         string
}

export interface TimeSeriesPoint {
  index:      number
  value:      number
  timestamp?: string
}

export interface Statistics {
  min:    number
  max:    number
  mean:   number
  std:    number
  median: number
}

export interface AnalysisResult {
  health_score:  number
  health_status: string
  fault:         string
  severity:      string
  confidence:    number
  risk_level:    string
  recommendation: string
  anomaly: {
    detected:   boolean
    count:      number
    percentage: number
    mean_score: number
  }
  risk: {
    days_7:  number
    days_30: number
    level:   string
  }
  trends: {
    temperature: string
    vibration:   string
    current:     string
    voltage:     string
    power:       string
  }
  statistics: {
    temperature?: Statistics
    vibration?:   Statistics
    current?:     Statistics
    voltage?:     Statistics
    power?:       Statistics
    load?:        Statistics
    health_score?: Statistics
  }
  time_series: {
    temperature: TimeSeriesPoint[]
    vibration:   TimeSeriesPoint[]
    current:     TimeSeriesPoint[]
    voltage:     TimeSeriesPoint[]
    power:       TimeSeriesPoint[]
    load:        TimeSeriesPoint[]
    health_score: TimeSeriesPoint[]
  }
  fault_distribution:        { name: string; value: number }[]
  estimated_rated_current:   number
  iso_zone:                  string
  root_causes:               string[]
  health_timeline:           HealthTimelinePhase[]
  xai:                       XAIContribution[]
  rul:                       RULEstimate
  risk_factors:              string[]
  recommendations_prioritized: PrioritizedRecommendation[]
  xai_context?:              Record<string, number | string>
  motor_profile?:            MotorProfile | null
  correlation_matrix?:       CorrelationMatrix | null
  health_prediction?:        HealthPrediction | null
  fft_spectrum?:             FFTSpectrum | null
  autoencoder?:              AutoEncoderResult | null
}

export interface HealthPrediction {
  method:             string
  trajectory:         number[]
  predictions:        { day_7: number; day_14: number; day_30: number }
  trend_slope:        number
  trend_label:        string
  days_to_critical?:  string | null
  current_health:     number
}

export interface FFTSpectrum {
  spectrum:       { frequency: number; magnitude: number }[]
  dominant:       { frequency: number; magnitude: number }
  n_points:       number
  frequency_unit: string
  note:           string
}

export interface AutoEncoderResult {
  method:                      string
  n_anomalies:                 number
  pct_anomalies:               number
  mean_reconstruction_error:   number
  threshold:                   number
  explained_variance?:         number
}

export interface HealthTimelinePhase {
  phase:      string
  avg_health: number
  start_pct:  number
  end_pct:    number
}

export interface XAIContribution {
  feature:      string
  contribution: number
}

export interface RULEstimate {
  value:      string
  days:       number | null
  confidence: string
  label:      string
}

export interface PrioritizedRecommendation {
  priority: number
  action:   string
  urgency:  'immediate' | 'days' | 'weeks' | 'months'
}

export interface AnalyzeResponse {
  report_id:    string
  status:       string
  analysis:     AnalysisResult
  ai_narrative: string | null
}

export interface ListReportEntry {
  report_id:     string
  filename:      string
  status:        string
  row_count:     number
  quality_score: number
  health_score:  number | null
  risk_7d:       number | null
  fault:         string | null
  severity:      string | null
  created_at:    string
  analyzed_at:   string | null
}

export interface ReportDetail {
  report_id:      string
  filename:       string
  file_size:      number
  row_count:      number
  column_count:   number
  missing_values: number
  quality_score:  number
  status:         string
  columns:        string[]
  preview:        Record<string, unknown>[]
  analysis:       AnalysisResult
  ai_narrative:   string | null
  created_at:     string
  analyzed_at:    string | null
}

export type WorkflowStep = 'upload' | 'preview' | 'analyzing' | 'results' | 'history'

export interface MotorProfile {
  name?:               string
  manufacturer?:       string
  nominal_power_kw?:   number
  nominal_voltage_v?:  number
  nominal_current_a?:  number
  nominal_speed_rpm?:  number
  insulation_class?:   string
  efficiency_class?:   string
  protection_class?:   string
}

export interface CorrelationMatrix {
  labels: string[]
  matrix: number[][]
}

export interface HistoryEntry {
  report_id:    string
  filename:     string
  analyzed_at:  string
  health_score: number | null
  risk_7d:      number | null
  fault:        string | null
  severity:     string | null
}

// ── French translations ─────────────────────────────────────────────────────

export const FAULT_FR: Record<string, string> = {
  'No Fault':          'Aucun Défaut',
  'Early Degradation': 'Dégradation Précoce',
  'Bearing Wear':      'Usure des Roulements',
  'Misalignment':      'Désalignement',
  'Unbalance':         'Déséquilibre Rotor',
  'Rotor Fault':       'Défaut Rotor',
  'Insulation Fault':  "Défaut d'Isolation",
  'Overload':          'Surcharge',
}

export const HEALTH_STATUS_FR: Record<string, string> = {
  'Healthy': 'Sain',
  'Warning': 'Avertissement',
  'Critical': 'Critique',
}

export const SEVERITY_FR: Record<string, string> = {
  'LOW':      'FAIBLE',
  'MEDIUM':   'MOYEN',
  'HIGH':     'ÉLEVÉ',
  'CRITICAL': 'CRITIQUE',
}

export const TREND_FR: Record<string, string> = {
  'RISING':  'HAUSSE',
  'FALLING': 'BAISSE',
  'STABLE':  'STABLE',
}

export const REC_FR: Record<string, string> = {
  'Bearing Wear':      "Inspecter les roulements, vérifier la lubrification et planifier le remplacement si les vibrations restent élevées.",
  'Misalignment':      "Réaliser un alignement d'arbre, inspecter l'accouplement et vérifier l'état de la semelle.",
  'Unbalance':         "Inspecter l'équilibre du rotor, nettoyer les surfaces du ventilateur et vérifier les jeux.",
  'Rotor Fault':       "Vérifier les barres du rotor, analyser la signature de courant et planifier des tests électriques.",
  'Insulation Fault':  "Effectuer des tests de résistance d'isolement, vérifier les voies de refroidissement et l'état des bobinages.",
  'Overload':          "Réduire la charge, vérifier le dimensionnement du moteur, inspecter l'équipement entraîné et revoir le cycle de service.",
  'Early Degradation': "Dégradation précoce détectée. Inspecter l'équilibre du rotor et l'état des roulements. Planifier une maintenance préventive dans les 30 jours.",
  'No Fault':          "Aucun défaut détecté. Continuer la surveillance normale et examiner les tendances lors de la prochaine inspection.",
}
