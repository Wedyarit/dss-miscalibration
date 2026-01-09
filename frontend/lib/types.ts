export interface Question {
  id: number;
  stem: string;
  options: string[];
  correct_option: number;
  tags: string[];
  difficulty_hint?: number;
  created_at: string;
}

export interface Session {
  id: number;
  user_id: number;
  mode: 'standard' | 'self_confidence';
  created_at: string;
  finished_at?: string;
}

export interface AnswerResponse {
  is_correct: boolean;
  correct_option: number;
  feedback: string;
  session_id: number;
}

export interface PredictionResponse {
  risk: number;
  recommendation: string;
  model_version?: string;
  features_used?: number;
  error?: string;
}

export interface AnalyticsOverview {
  ece: number;
  mce: number;
  brier: number;
  roc_auc: number;
  confident_error_rate: number;
  total_interactions: number;
  interactions_with_confidence: number;
  model_version?: string;
}

export interface ReliabilityBin {
  bin_low: number;
  bin_high: number;
  conf_avg: number;
  acc_avg: number;
  count: number;
}

export interface ReliabilityResponse {
  bins: ReliabilityBin[];
  n_bins: number;
  model_version?: string;
}

export interface ProblematicItem {
  item_id: number;
  stem: string;
  tags: string[];
  confident_error_rate: number;
  total_interactions: number;
  avg_confidence: number;
  avg_accuracy: number;
}

export interface TrainRequest {
  confidence_threshold: number;
  calibration: 'platt' | 'isotonic' | 'none';
  bins: number;
  test_size?: number;
}

export interface TrainResponse {
  success: boolean;
  model_version?: string;
  metrics?: Record<string, number>;
  n_samples?: number;
  n_features?: number;
  model_id?: number;
  error?: string;
}
