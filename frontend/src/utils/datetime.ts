const TIMEZONE_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/i

/**
 * 后端历史数据中的时间是不带时区的 UTC 字符串。
 * 浏览器会把这种字符串当成本地时间，因此需要补上 Z 后再解析。
 */
export function parseServerDate(value: string): Date {
  return new Date(TIMEZONE_SUFFIX.test(value) ? value : `${value}Z`)
}
