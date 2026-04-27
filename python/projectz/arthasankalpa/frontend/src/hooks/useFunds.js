/**
 * useFunds.js - Fund search, recommendations, and budget analysis hooks.
 */
import { useState, useCallback } from "react";
import { fundsApi, budgetApi } from "../services/api";

export function useFundSearch() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const search = useCallback(async (params) => {
    if (!params.q || !params.q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fundsApi.search(params);
      setResults(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search, setResults };
}

export function useRecommendations(userId) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const fetch = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fundsApi.recommendations(userId);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  return { data, loading, error, fetch };
}

export function useBudgetAnalysis() {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const analyze = useCallback(async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await budgetApi.analyze(formData);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, analyze };
}