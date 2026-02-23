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
  purpose?: 'calibration' | 'real';
  created_at: string;
  finished_at?: string;
}

export interface AnswerResponse {
  is_correct: boolean;
  correct_option: number;
  feedback: string;
  session_id: number;
}

export interface AnswerSubmitPayload {
  item_id: number;
  chosen_option: number;
  confidence?: number;
  initial_chosen_option?: string;
  initial_confidence?: number;
  reconsidered?: boolean;
  time_to_reconsider_ms?: number;
  response_time_ms: number;
  answer_changes_count?: number;
  time_to_first_choice_ms?: number;
  time_after_choice_ms?: number;
}

export interface PredictionResponse {
  intervention: {
    risk: number;
    reason_code: string;
    message_ru: string;
    show_intervention: boolean;
    reason_text?: string;
  };
  model_version?: string;
  features_used?: number;
  error?: string;
}

export interface SimulatedUser {
  user_id: number;
  student_name: string;
  is_new: boolean;
}

export interface ConfidencePolicyResponse {
  should_request_confidence: boolean;
  confidence_sampling_rate: number;
  mode: 'standard' | 'self_confidence';
}

export interface NextQuestionResponse {
  question: Question;
  require_confidence: boolean;
}

export interface AnalyticsOverview {
  ece: number;
  mce: number;
  brier: number;
  roc_auc: number;
  confident_error_rate: number;
  total_interactions: number;
  interactions_with_confidence: number;
  coachability_rate: number;
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
  pedagogical_note?: string;
  recommendation_for_teacher?: string;
}

export interface HiddenStar {
  user_id: number;
  student_name: string;
  accuracy: number;
  avg_confidence: number;
}

export interface InstructorInsight {
  key: string;
  label: string;
  value: string;
  description: string;
}

export interface InstructorSummary {
  overview: AnalyticsOverview;
  reliability: ReliabilityResponse;
  class_self_awareness: string;
  danger_zones: string[];
  hidden_stars: HiddenStar[];
  insights: InstructorInsight[];
  problematic_items: ProblematicItem[];
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
