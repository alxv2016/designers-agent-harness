import type { ButtonHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'
import styles from './button.module.css'

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>

/**
 * An action — DESIGN.md's `Button`. A native <button>, so its role, the keyboard and focus come with it; `type` is
 * "button" unless it submits a form. Every state's value is a token (button.module.css).
 */
export function Button({ type = 'button', className, ...props }: ButtonProps) {
  return (
    <button type={type} className={cx(styles.button, className)} {...props} />
  )
}
