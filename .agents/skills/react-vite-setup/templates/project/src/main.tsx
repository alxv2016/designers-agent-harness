import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from '@/app/App'
import './styles/tokens.css'
import './styles/global.css'

// The one entry: the tokens and the styles every screen shares, then the app shell (APP_ARCHITECTURE §1).
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
