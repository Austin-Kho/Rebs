interface BCParent {
  pk: number
  name: string
  slug: string
}

export interface SimpleMember {
  pk: number
  user: { pk: number; username: string }
  roles: { pk: number; name: string }[]
  add_roles?: { pk: number; name: string }[]
}

export interface IssueProject {
  pk?: number
  company: number
  name: string
  slug: string
  description: string
  homepage: string | null
  is_public: boolean
  family_tree?: BCParent[]
  parent: number | null
  sub_projects?: IssueProject[]
  module?: Module | null
  is_inherit_members: boolean
  allowed_roles?: { pk: number; name: string }[]
  trackers?: { pk: number; name: string; description: string }[]
  versions?: Version[]
  default_version: string | null
  categories?: { pk: number; name: string; assigned_to: { pk: number; username: string } | null }[]
  status: '1' | '9'
  depth: number
  all_members?: SimpleMember[]
  members?: SimpleMember[]
  visible?: boolean
  total_estimated_hours?: number
  total_time_spent?: number
  user?: string
  created?: string
  updated?: string
}

export interface ProjectFilter {
  parent__isnull?: boolean
  parent?: string
  status?: '1' | '9'
  status__exclude?: '1' | '9'
  project?: string
  project__exclude?: string
  is_public?: '1' | '0'
  is_public__exclude?: '1' | '0'
  name?: string
  description?: string
}

export interface Module {
  pk?: number
  project: number
  issue: boolean
  time: boolean
  news: boolean
  document: boolean
  file: boolean
  wiki: boolean
  repository: boolean
  forum: boolean
  calendar: boolean
  gantt: boolean
}

export interface Role {
  pk: number
  name: string
  assignable: boolean
  issue_visible: 'ALL' | 'PUB' | 'PRI'
  time_entry_visible: 'ALL' | 'PRI'
  user_visible: 'ALL' | 'PRJ'
  default_time_activity: number | null
  permission: Permission
  order: number
  user: number
  created: string
  updated: string
}

export interface Permission {
  pk: 1
  project_create: boolean
  project_update: boolean
  project_close: boolean
  project_delete: boolean
  project_public: boolean
  project_module: boolean
  project_member: boolean
  project_version: boolean
  project_create_sub: boolean
  project_pub_query: boolean
  project_save_query: boolean
  forum_read: boolean
  forum_create: boolean
  forum_update: boolean
  forum_own_update: boolean
  forum_delete: boolean
  forum_own_delete: boolean
  forum_watcher_read: boolean
  forum_watcher_create: boolean
  forum_watcher_delete: boolean
  forum_manage: boolean
  calendar_read: boolean
  document_read: boolean
  document_create: boolean
  document_update: boolean
  document_delete: boolean
  file_read: boolean
  file_manage: boolean
  gantt_read: boolean
  issue_read: boolean
  issue_create: boolean
  issue_update: boolean
  issue_own_update: boolean
  issue_copy: boolean
  issue_rel_manage: boolean
  issue_sub_manage: boolean
  issue_public: boolean
  issue_own_public: boolean
  issue_comment_create: boolean
  issue_comment_update: boolean
  issue_comment_own_update: boolean
  issue_private_comment_read: boolean
  issue_private_comment_set: boolean
  issue_delete: boolean
  issue_watcher_read: boolean
  issue_watcher_create: boolean
  issue_watcher_delete: boolean
  issue_import: boolean
  issue_category_manage: boolean
  news_read: boolean
  news_manage: boolean
  news_comment: boolean
  repo_changesets_read: boolean
  repo_read: boolean
  repo_commit_access: boolean
  repo_rel_issue_manage: boolean
  repo_manage: boolean
  time_read: boolean
  time_create: boolean
  time_update: boolean
  time_own_update: boolean
  time_pro_act_manage: boolean
  time_other_user_log: boolean
  time_entries_import: boolean
  wiki_read: boolean
  wiki_history_read: boolean
  wiki_page_export: boolean
  wiki_page_update: boolean
  wiki_page_rename: boolean
  wiki_page_delete: boolean
  wiki_attachment_delete: boolean
  wiki_watcher_read: boolean
  wiki_watcher_create: boolean
  wiki_watcher_delete: boolean
  wiki_page_project: boolean
  wiki_manage: boolean
}

export interface Member {
  pk: number
  user: { pk: number; username: string }
  roles: { pk: number; name: string }[]
}

export interface Version {
  pk?: number
  project?: string
  name: string
  status: '1' | '2' | '3'
  status_desc?: '진행' | '잠김' | '닫힘'
  sharing: '0' | '1' | '2' | '3' | '4'
  sharing_desc?:
    | '공유 없음'
    | '하위 프로젝트'
    | '상위 및 하위 프로젝트'
    | '최상위 및 모든 하위 프로젝트'
    | '모든 프로젝트'
  effective_date: string | null
  description: string
  wiki_page_title: string
}

export interface Tracker {
  pk: number
  name: string
  description: string
  is_in_roadmap: boolean
  default_status: number
  projects: number[]
  order: number
}

export interface IssueStatus {
  pk: number
  name: string
  description: string
  closed: boolean
  order: number
}

export interface CodeValue {
  pk: number
  name: string
  active: boolean
  default: boolean
  order: number
}

export interface IssueFile {
  pk: number
  file: string
  file_name: string
  file_type: string
  file_size: number
  description: string
  created: string
  user: {
    pk: number
    username: string
  }
  cngFile?: File | null
  del?: boolean
  edit?: boolean
}

export interface SubIssue {
  pk: number
  subject: string
  status: string
  assigned_to: { pk: number; username: string }
  start_date: string
  estimated_hours: string | null
  done_ratio: number
  closed: string | null
}

export interface Issue {
  pk: number
  project: { slug: string; name: string }
  tracker: { pk: number; name: string; description: string }
  status: { pk: number; name: string }
  priority: { pk: number; name: string }
  subject: string
  description: string
  category: number | null
  fixed_version: number | null
  assigned_to: { pk: number; username: string } | null
  parent: number | null
  watchers: { pk: number; username: string }[]
  is_private: boolean
  estimated_hours: number | null
  start_date: string | null
  due_date: string | null
  done_ratio: number
  closed: string | null
  spent_time: number | null
  files: Array<IssueFile>
  sub_issues: SubIssue[]
  related_issues: IssueRelation[]
  creator: { pk: number; username: string }
  updater: { pk: number; username: string } | null
  created: string
  updated: string
}

export interface IssueFilter {
  status__closed?: '' | '0' | '1' // '0: any' | '0: open' | '1: closed'
  status?: number | null
  status__exclude?: number | null
  project?: string
  project__search?: string
  project__exclude?: string
  tracker?: number | null
  tracker__exclude?: number | null
  parent?: number | string
  parent__subject?: string
  parent__isnull?: string
  page?: number
}

export interface IssueRelation {
  pk?: number
  issue: number
  issue_to: SubIssue | null
  relation_type:
    | 'relates'
    | 'duplicates'
    | 'duplicated'
    | 'blocks'
    | 'blocked'
    | 'precedes'
    | 'follows'
    | 'copied_to'
    | 'copied_from'
  type_display?: string
  delay: number | null
}

export interface IssueComment {
  pk: number
  issue: {
    pk: number
    project: { slug: string; name: string }
    tracker: string
    status: string
    subject: string
    description: string
  }
  content: string
  is_private: boolean
  created: string
  updated: string
  user: {
    pk: number
    username: string
  }
}

export interface TimeEntry {
  pk: number
  issue: {
    pk: number
    project: { slug: string; name: string }
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  }
  spent_on: string
  hours: string
  activity: { pk: number; name: string }
  comment: string
  created: string
  updated: string
  user: { pk: number; username: string }
  total_hours: number
}

export interface TimeEntryFilter {
  ordering?: string
  project?: string
  project__search?: string
  project__exclude?: string
  spent_on?: string
  from_spent_on?: string
  to_spent_on?: string
  issue?: number | ''
  issue__keyword?: string
  user?: number | ''
  user__exclude?: number | ''
  author?: number | ''
  activity?: number | ''
  hours?: number
  comment?: string
  tracker?: number | ''
  parent?: number | ''
  status?: number | ''
  version?: number | ''
  subject?: string
  project_status?: number | ''
  page?: number
}

export interface News {
  pk?: number
  project?: { slug: string; name: string }
  title: string
  summary: string
  description: string
  author?: { pk: number; username: string }
  created: string
}

export interface ActLogEntry {
  pk: number
  sort: '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'
  project: { slug: string; name: string } | null
  issue: {
    pk: number
    project: { slug: string; name: string }
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  } | null
  status_log: string
  comment: { pk: number; content: string } | null
  // change_sets: string
  // news: string
  // document: string
  // file: string
  // wiki: string
  // message: string
  spent_time: { pk: number; hours: string; comment: '' } | null
  act_date: string
  timestamp: string
  user: {
    pk: number
    username: string
  }
}

export interface ActLogEntryFilter {
  project?: string
  project__search?: string
  to_act_date?: string
  from_act_date?: string
  user?: string
  sort?: Array<'1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9'>
}

export interface IssueLogEntry {
  pk: number
  log_id: number
  issue: {
    pk: number
    project: { slug: string; name: string }
    tracker: string
    status: { pk: number; name: string; closed: boolean }
    subject: string
    description: string
  }
  action: string
  comment: { pk: number; content: string } | null
  details: string
  diff: string
  timestamp: string
  user: {
    pk: number
    username: string
  }
}
