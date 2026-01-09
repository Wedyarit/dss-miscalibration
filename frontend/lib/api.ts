import axios from 'axios';
import {
  AnalyticsOverview,
  AnswerResponse,
  PredictionResponse,
  ProblematicItem,
  Question,
  ReliabilityResponse,
  Session,
  TrainRequest,
  TrainResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Questions API
export const questionsApi = {
  create: async (question: Omit<Question, 'id' | 'created_at'>) => {
    const response = await api.post('/questions/', question);
    return response.data;
  },

  get: async (id: number, language = 'en'): Promise<Question> => {
    const response = await api.get(`/questions/${id}`, {
      params: { language },
    });
    return response.data;
  },

  getRandom: async (sessionId?: number, language = 'en'): Promise<Question> => {
    const params: Record<string, string | number> = { language };
    if (sessionId) params.session_id = sessionId;
    const response = await api.get('/questions/next/random', { params });
    return response.data;
  },

  list: async (skip = 0, limit = 100, tags?: string[], language = 'en') => {
    const params: Record<string, string | number> = { skip, limit, language };
    if (tags) params.tags = tags.join(',');
    const response = await api.get('/questions/', { params });
    return response.data;
  },
};

// Sessions API
export const sessionsApi = {
  create: async (userId: number, mode: 'standard' | 'self_confidence'): Promise<Session> => {
    const response = await api.post('/sessions/', {
      user_id: userId,
      mode,
    });
    return response.data;
  },

  get: async (id: number): Promise<Session> => {
    const response = await api.get(`/sessions/${id}`);
    return response.data;
  },

  submitAnswer: async (
    sessionId: number,
    itemId: number,
    chosenOption: number,
    confidence?: number,
    responseTimeMs?: number,
    language = 'en',
    answerChangesCount?: number,
    timeToFirstChoiceMs?: number,
    timeAfterChoiceMs?: number
  ): Promise<AnswerResponse> => {
    const response = await api.post(
      `/sessions/${sessionId}/answer`,
      {
        item_id: itemId,
        chosen_option: chosenOption,
        confidence,
        response_time_ms: responseTimeMs || 0,
        answer_changes_count: answerChangesCount,
        time_to_first_choice_ms: timeToFirstChoiceMs,
        time_after_choice_ms: timeAfterChoiceMs,
      },
      {
        params: { language },
      }
    );
    return response.data;
  },

  finish: async (sessionId: number) => {
    const response = await api.post(`/sessions/${sessionId}/finish`);
    return response.data;
  },
};

// Prediction API
export const predictionApi = {
  predict: async (
    userId: number,
    itemId: number,
    chosenOption: number,
    confidence?: number,
    responseTimeMs?: number
  ): Promise<PredictionResponse> => {
    const response = await api.post('/predict/', {
      user_id: userId,
      item_id: itemId,
      chosen_option: chosenOption,
      confidence,
      response_time_ms: responseTimeMs || 0,
      attempts_count: 1,
    });
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  getOverview: async (): Promise<AnalyticsOverview> => {
    const response = await api.get('/analytics/overview');
    return response.data;
  },

  getReliability: async (nBins = 10): Promise<ReliabilityResponse> => {
    const response = await api.get('/analytics/reliability', {
      params: { n_bins: nBins },
    });
    return response.data;
  },

  getProblematicItems: async (
    threshold = 0.7,
    minInteractions = 5,
    language = 'en'
  ): Promise<{ items: ProblematicItem[] }> => {
    const response = await api.get('/analytics/items/problematic', {
      params: { threshold, min_interactions: minInteractions, language },
    });
    return response.data;
  },

  exportInteractions: async (
    startDate?: string,
    endDate?: string,
    userId?: number,
    sessionId?: number
  ) => {
    const params: Record<string, string | number> = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (userId) params.user_id = userId;
    if (sessionId) params.session_id = sessionId;

    const response = await api.get('/analytics/export/interactions', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};

// Admin API
export const adminApi = {
  seedDatabase: async (): Promise<{
    message: string;
    users_created: number;
    questions_created: number;
    sessions_created: number;
    interactions_created: number;
  }> => {
    const response = await api.post(
      '/ingest/seed',
      {},
      {
        headers: { 'X-API-Key': 'dev-key' },
      }
    );
    return response.data;
  },

  trainModel: async (request: TrainRequest): Promise<TrainResponse> => {
    const response = await api.post('/train/', request, {
      headers: { 'X-API-Key': 'dev-key' },
    });
    return response.data;
  },
};
