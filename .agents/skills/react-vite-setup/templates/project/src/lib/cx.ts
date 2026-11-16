/** Joins class names, skipping the empty ones: `cx(styles.button, active && styles.active)`. */
export function cx(...names: Array<string | false | null | undefined>): string {
  return names.filter(Boolean).join(' ')
}
