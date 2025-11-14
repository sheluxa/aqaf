
export async function callApi(path: string, body: any) {
  const base = process.env.AQA_API_BASE || 'http://localhost:8787';
  const res = await fetch(base + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return await res.json();
}
