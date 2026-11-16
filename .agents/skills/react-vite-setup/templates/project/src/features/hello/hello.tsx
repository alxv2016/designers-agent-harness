import { useState } from 'react'
import { Button } from '@/components/ui/button'
import styles from './hello.module.css'

/**
 * The hello-world feature: a heading, a line of text, and a button that counts its presses. It has the shape every
 * feature takes — its own folder and styles, its controls from components/ui — and goes when the first real feature
 * lands, with the smoke test's lines that name it (APP_ARCHITECTURE §4).
 */
export function Hello() {
  const [count, setCount] = useState(0)

  return (
    <section className={styles.hello} aria-labelledby="hello-title">
      <h1 id="hello-title" className={styles.title}>
        Hello world
      </h1>
      <p className={styles.lead}>
        Edit src/features/hello/hello.tsx and save to see it change.
      </p>
      <Button onClick={() => setCount((n) => n + 1)}>Add one</Button>
      <output className={styles.count}>Count: {count}</output>
    </section>
  )
}
