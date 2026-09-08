import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../services/api';

/**
 * Generic data-fetching hook.
 *
 *   const { data, loading, error, refresh } = useApi('/api/risk/zones', { pollMs: 30000 });
 *
 * pollMs > 0 enables automatic background refresh - dashboard & monitoring
 * pages use this so simulated runs visibly update every screen.
 */
export function useApi(path, { pollMs = 0, enabled = true, initial = null } = {}) {
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(Boolean(enabled && initial === null));
  const [error, setError] = useState(null);
  const timer = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const result = await api.get(path);
      setData(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Request failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    if (!enabled) return undefined;
    let active = true;
    setLoading(true);
    api
      .get(path)
      .then((result) => {
        if (active) {
          setData(result);
          setError(null);
        }
      })
      .catch((err) => {
        if (active) setError(err instanceof ApiError ? err.message : 'Request failed');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [path, enabled]);

  useEffect(() => {
    if (!enabled || pollMs <= 0) return undefined;
    timer.current = setInterval(() => {
      api
        .get(path)
        .then((result) => {
          setData(result);
          setError(null);
        })
        .catch(() => {
          /* silent background refresh */
        });
    }, pollMs);
    return () => clearInterval(timer.current);
  }, [path, pollMs, enabled]);

  return { data, loading, error, refresh };
}

/** Shortcut for mutations that trigger a refresh afterwards. */
export function useMutate(refresh) {
  return useCallback(
    async (path, body, method = 'POST') => {
      try {
        const result =
          method === 'PUT'
            ? await api.put(path, body)
            : method === 'DELETE'
              ? await api.del(path)
              : await api.post(path, body);
        refresh && (await refresh());
        return { ok: true, result };
      } catch (err) {
        return { ok: false, message: err instanceof ApiError ? err.message : 'Request failed' };
      }
    },
    [refresh],
  );
}
