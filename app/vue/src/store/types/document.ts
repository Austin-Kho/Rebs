export interface Group {
  pk: number | null
  name: string
  manager: number[]
}

export interface Board {
  pk: number | null
  group: number | null
  name: string
  order: number | null
  search_able: boolean
  manager: number[]
}

export interface Category {
  pk: number | null
  board: number | null
  color: string | null
  name: string
  parent: number | null
  order: number | null
}

export interface SuitCase {
  pk: number | null
  company: number | null
  project: number | null
  proj_name?: string
  sort: '' | '1' | '2' | '3' | '4' | '5'
  sort_desc?: string
  level: '' | '0' | '1' | '2' | '3'
  level_desc?: string
  related_case: number | null
  related_case_name?: string
  court: string
  court_desc?: string
  other_agency: string
  case_number: string
  case_name: string
  plaintiff: string
  plaintiff_attorney: string
  defendant: string
  defendant_attorney: string
  related_debtor: string
  case_start_date: string | null
  case_end_date: string | null
  summary: string
  user?: string
  links?: Array<{ pk: number; category: { name: string; color?: string }; link: string }>
  files?: Array<{ pk: number; category: { name: string; color?: string }; file: string }>
  created?: string
  prev_pk?: number | null
  next_pk?: number | null
}

export interface SimpleSuitCase {
  pk: number | null
  __str__: string
}

export type Post = {
  [key: string]: undefined | number | number[] | null | string | boolean | Link[] | AFile[]
  pk?: number
  company: number | null
  project: number | null
  board: number | null
  is_notice: boolean
  proj_name?: string | null
  category: number | null
  cate_name?: string | null
  lawsuit: number | null | string
  lawsuit_name?: string | null
  title: string
  execution_date: string | null
  content: string
  is_hide_comment: boolean
  hit: number
  blame: number
  ip: string | null
  device: string
  secret: boolean
  password: string
  links?: Link[]
  files?: AFile[]
  comments?: number[]
  user?: number | null
  soft_delete?: string | null
  created?: string
  updated?: string
  is_new?: boolean
  prev_pk?: number | null
  next_pk?: number | null
}

export interface Link {
  pk: null | number
  post: number
  link: string
  hit: number
  del?: boolean
}

export interface AFile {
  pk: null | number
  post?: number
  file?: string
  newFile?: Blob
  hit: number
  del?: boolean
}

export type Attatches = {
  newLinks: Link[]
  newFiles?: (string | File)[]
  cngFiles?: {
    pk: number
    file: File
  }[]
}

export interface PatchPost {
  pk: number
  is_notice?: boolean
  category?: number | null
  lawsuit?: number | null
  title?: string
  execution_date?: string | null
  content?: string
  is_hide_comment?: boolean
  hit?: number
  like?: number[]
  dislike?: number[]
  blame?: number
  secret?: boolean
  password?: string
  soft_delete?: string | null
}
