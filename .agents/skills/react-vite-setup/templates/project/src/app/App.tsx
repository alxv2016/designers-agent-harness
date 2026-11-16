import { Hello } from '@/features/hello/hello'
import styles from './app.module.css'

/**
 * The app shell: the page's frame, and which feature fills it. Features meet here and nowhere else — one never
 * imports another (APP_ARCHITECTURE §2). A router joins here when there is a second page.
 */
export function App() {
  return (
    <main className={styles.main}>
      <Hello />
    </main>
  )
}
