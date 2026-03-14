import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import './i18n'
import App from './App.jsx'

// ── Capture uncaught runtime errors so they show on screen ───
const errBox = () => {
  let el = document.getElementById('__rt_err');
  if (!el) {
    el = document.createElement('div');
    el.id = '__rt_err';
    Object.assign(el.style, {
      position: 'fixed', bottom: '1rem', left: '1rem', right: '1rem',
      zIndex: 99999, background: '#1a0000', color: '#F87171',
      border: '1px solid #7f1d1d', borderRadius: '0.5rem',
      padding: '0.75rem 1rem', fontSize: '0.75rem', fontFamily: 'monospace',
      maxHeight: '8rem', overflow: 'auto', whiteSpace: 'pre-wrap',
    });
    document.body.appendChild(el);
  }
  return el;
};
window.addEventListener('error', (e) => {
  if (e.filename?.startsWith('chrome-extension://')) return;
  errBox().textContent = `[Error] ${e.message}\n${e.filename}:${e.lineno}`;
});
window.addEventListener('unhandledrejection', (e) => {
  const msg = e.reason?.message || String(e.reason || '');
  if (msg.includes('MetaMask') || msg.includes('chrome-extension')) return;
  errBox().textContent = `[Promise] ${msg}\n${e.reason?.stack || ''}`;
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter basename="/app">
      <App />
    </BrowserRouter>
  </StrictMode>,
)
