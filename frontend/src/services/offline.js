/** Offline field-report queue (localStorage based).
 *
 * When the device is offline, reports are stored locally (photo embedded
 * as data URL). On reconnect the app calls syncPendingReports() and pushes
 * each queued report to the backend.
 */
import { api } from './api';

const QUEUE_KEY = 'ner_pending_reports';

export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

export function getPendingReports() {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveQueue(items) {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
  } catch {
    /* storage may be full (large images) - drop nothing, log silently */
  }
}

export function queueReport(report) {
  const queue = getPendingReports();
  queue.push({ ...report, queuedAt: new Date().toISOString(), localId: `q_${Date.now()}` });
  saveQueue(queue);
  return queue.length;
}

export function removeQueuedReport(localId) {
  saveQueue(getPendingReports().filter((r) => r.localId !== localId));
}

export async function syncPendingReports(onProgress) {
  const queue = getPendingReports();
  const failed = [];
  for (const item of queue) {
    try {
      const form = new FormData();
      form.append('report_type', item.report_type || 'OTHER');
      form.append('description', item.description || '');
      form.append('latitude', String(item.latitude));
      form.append('longitude', String(item.longitude));
      if (item.imageData) {
        const blob = await (await fetch(item.imageData)).blob();
        form.append('image', blob, item.imageName || 'report.jpg');
      }
      await api.postForm('/api/reports', form);
      removeQueuedReport(item.localId);
      onProgress && onProgress(getPendingReports().length);
    } catch {
      failed.push(item);
    }
  }
  return { synced: queue.length - failed.length, failed: failed.length };
}

export function subscribeOnline(cb) {
  window.addEventListener('online', cb);
  return () => window.removeEventListener('online', cb);
}
