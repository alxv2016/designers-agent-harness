import { describe, expect, it } from 'vitest'
import { cx } from './cx'

describe('cx', () => {
  it('joins the names it is given', () => {
    expect(cx('a', 'b')).toBe('a b')
  })

  it('skips the empty ones', () => {
    expect(cx('a', false, null, undefined, '', 'b')).toBe('a b')
  })
})
