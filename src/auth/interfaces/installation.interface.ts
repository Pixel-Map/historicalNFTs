export interface Installation {
  access_tokens_url: string;
  account: Account;
  app_id: number;
  app_slug: string;
  created_at: string;
  events?: (string)[] | null;
  html_url: string;
  id: number;
  permissions: Permissions;
  repositories_url: string;
  repository_selection: string;
  single_file_name?: null;
  target_id: number;
  target_type: string;
  updated_at: string;
}
export interface Account {
  avatar_url: string;
  events_url: string;
  followers_url: string;
  following_url: string;
  gists_url: string;
  gravatar_id: string;
  html_url: string;
  id: number;
  login: string;
  node_id: string;
  organizations_url: string;
  received_events_url: string;
  repos_url: string;
  site_admin: boolean;
  starred_url: string;
  subscriptions_url: string;
  type: string;
  url: string;
}
export interface Permissions {
  actions: string;
  administration: string;
  checks: string;
  contents: string;
  issues: string;
  members: string;
  metadata: string;
  organization_administration: string;
  pull_requests: string;
  repository_hooks: string;
  statuses: string;
}
