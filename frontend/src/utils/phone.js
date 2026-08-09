export function normalizePhone(raw) {
  if (!raw) return raw
  return raw.replace(/[\s-]/g, '').replace(/^\+91/, '').replace(/^0+/, '')
}