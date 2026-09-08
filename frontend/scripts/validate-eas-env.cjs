const value = process.env.EXPO_PUBLIC_API_URL;
let url;
try { url = new URL(value); } catch {}
if (!url || url.protocol !== 'https:' || /localhost|127\.0\.0\.1|REPLACE-WITH/i.test(url.hostname) || !url.pathname.replace(/\/$/, '').endsWith('/api/v1')) {
  console.error('Set EXPO_PUBLIC_API_URL to the deployed HTTPS backend /api/v1 URL in your EAS build environment.');
  process.exit(1);
}
console.log('EAS API address is configured.');
