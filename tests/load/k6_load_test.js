import http from 'k6/http';
import { check, sleep } from 'k6';

/**
 * VERA Load Test Script (k6)
 *
 * Scenarios:
 * 1. Warm-up: 10 rps
 * 2. Medium load: 50 rps
 * 3. Peak / Breaking point test: 100 rps
 *
 * Objectives:
 * - Measure latency: p50, p95, p99
 * - Verify rate limiting triggers 429/503 gracefully rather than crashing
 * - Confirm zero 500 errors on valid inputs
 */

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp to 10 RPS
    { duration: '1m', target: 50 },   // Ramp to 50 RPS
    { duration: '30s', target: 100 }, // Peak at 100 RPS
    { duration: '30s', target: 0 },   // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1500', 'p(99)<3000'], // 95% under 1.5s
    http_req_failed: ['rate<0.15'], // Less than 15% failures (accounting for rate-limits)
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test Health Endpoint (Cheap read)
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });

  // Test Public Evidence Verification
  const payload = JSON.stringify({
    evidence_type: 'text',
    content: 'Guaranteed 50% monthly returns on WhatsApp VIP Stock Club. Contact +91 9999999999.',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': `k6-${__VU}-${__ITER}`,
    },
  };

  const verifyRes = http.post(`${BASE_URL}/api/v1/investigations/verify-evidence`, payload, params);
  check(verifyRes, {
    'verify status is 200, 429, or 503': (r) => [200, 429, 503].includes(r.status),
    'no unhandled internal error (500)': (r) => r.status !== 500,
  });

  sleep(1);
}
