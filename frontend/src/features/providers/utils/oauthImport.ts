export interface ImportFileDescriptor {
  name: string
  type?: string
}

export interface ImportFileContent {
  name: string
  content: string
}

function looksLikeJson(text: string): boolean {
  const trimmed = text.trim()
  const firstChar = trimmed.charAt(0)
  return firstChar === '{' || firstChar === '['
}

function splitPlainTextItems(text: string): string[] {
  const lines = text
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(line => line && line.charAt(0) !== '#')

  return lines.length > 1 ? lines : [text.trim()]
}

function normalizeJsonBatchItems(
  value: unknown,
  fileName: string
): Array<Record<string, unknown> | string> {
  if (Array.isArray(value)) {
    const result: Array<Record<string, unknown> | string> = []
    value.forEach((item: unknown) => {
      result.push(...normalizeJsonBatchItems(item, fileName))
    })
    return result
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      throw new Error(`文件 ${fileName} 中包含空字符串内容`)
    }
    return [trimmed]
  }

  if (typeof value === 'object' && value !== null) {
    return [value as Record<string, unknown>]
  }

  throw new Error(`文件 ${fileName} 必须是 JSON 对象、字符串或对象数组`)
}

function toBatchItems(file: ImportFileContent): Array<Record<string, unknown> | string> {
  const trimmed = file.content.trim()
  if (!trimmed) {
    throw new Error(`文件 ${file.name} 不能为空`)
  }

  if (looksLikeJson(trimmed)) {
    try {
      return normalizeJsonBatchItems(JSON.parse(trimmed), file.name)
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '未知错误'
      throw new Error(`文件 ${file.name} JSON 格式无效：${message}`)
    }
  }

  return splitPlainTextItems(trimmed)
}

export function isSupportedImportFile(file: ImportFileDescriptor): boolean {
  const lowerName = file.name.toLowerCase()
  return (
    /\.json$/i.test(lowerName)
    || /\.txt$/i.test(lowerName)
    || file.type === 'application/json'
    || file.type === 'text/plain'
  )
}

export function buildImportTextFromFiles(files: ImportFileContent[]): string {
  if (files.length === 0) {
    throw new Error('请选择至少一个授权文件')
  }

  if (files.length === 1) {
    const onlyContent = files[0].content.trim()
    if (!onlyContent) {
      throw new Error(`文件 ${files[0].name} 不能为空`)
    }
    return files[0].content
  }

  const batchItems: Array<Record<string, unknown> | string> = []
  files.forEach((file: ImportFileContent) => {
    batchItems.push(...toBatchItems(file))
  })

  if (batchItems.length === 0) {
    throw new Error('未找到可导入的授权数据')
  }

  return JSON.stringify(batchItems, null, 2)
}

export function summarizeImportFiles(fileNames: string[]): string {
  if (fileNames.length === 0) return ''
  if (fileNames.length === 1) return fileNames[0]

  const preview = fileNames.slice(0, 3).join('、')
  return fileNames.length > 3
    ? `${preview} 等 ${fileNames.length} 个文件`
    : preview
}
