import { describe, expect, it } from 'vitest'

import {
  buildImportTextFromFiles,
  isSupportedImportFile,
  summarizeImportFiles,
} from '../oauthImport'

describe('oauthImport utils', () => {
  it('aggregates multiple json files into a json array payload', () => {
    const result = buildImportTextFromFiles([
      {
        name: 'account-a.json',
        content: JSON.stringify({ refresh_token: 'token-a', name: 'account-a' }),
      },
      {
        name: 'account-b.json',
        content: JSON.stringify({ auth_config: { refresh_token: 'token-b' }, email: 'b@example.com' }),
      },
    ])

    expect(JSON.parse(result)).toEqual([
      { refresh_token: 'token-a', name: 'account-a' },
      { auth_config: { refresh_token: 'token-b' }, email: 'b@example.com' },
    ])
  })

  it('splits multiline text content into independent batch items', () => {
    const result = buildImportTextFromFiles([
      { name: 'token-a.txt', content: 'token-a' },
      { name: 'token-b.txt', content: 'token-b\n# ignored\ntoken-c' },
    ])

    expect(JSON.parse(result)).toEqual(['token-a', 'token-b', 'token-c'])
  })

  it('throws on invalid json content when batch importing multiple files', () => {
    expect(() => buildImportTextFromFiles([
      { name: 'good.json', content: JSON.stringify({ refresh_token: 'token-a' }) },
      { name: 'bad.json', content: '{invalid json}' },
    ])).toThrow(/bad\.json/)
  })

  it('keeps single file content unchanged', () => {
    const content = '{\n  "refresh_token": "token-a"\n}'
    expect(buildImportTextFromFiles([{ name: 'single.json', content }])).toBe(content)
  })

  it('validates supported import file types', () => {
    expect(isSupportedImportFile({ name: 'a.json', type: '' })).toBe(true)
    expect(isSupportedImportFile({ name: 'a.txt', type: '' })).toBe(true)
    expect(isSupportedImportFile({ name: 'a.bin', type: 'application/json' })).toBe(true)
    expect(isSupportedImportFile({ name: 'a.bin', type: 'application/octet-stream' })).toBe(false)
  })

  it('summarizes selected file names for display', () => {
    expect(summarizeImportFiles(['a.json'])).toBe('a.json')
    expect(summarizeImportFiles(['a.json', 'b.json', 'c.json'])).toBe('a.json、b.json、c.json')
    expect(summarizeImportFiles(['a.json', 'b.json', 'c.json', 'd.json'])).toBe('a.json、b.json、c.json 等 4 个文件')
  })
})
