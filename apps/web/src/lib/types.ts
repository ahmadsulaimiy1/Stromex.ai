export type ConversationMode =
  | "general"
  | "research"
  | "quran"
  | "arabic_learning"
  | "book_writing";

export type MessageRole = "user" | "assistant" | "system";

export interface UserRead {
  id: string;
  email: string;
  display_name: string;
  role: "user" | "admin";
  preferred_language: string;
  is_active: boolean;
  is_guest: boolean;
  is_verified: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ConversationRead {
  id: string;
  title: string;
  mode: ConversationMode;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageRead {
  id: string;
  role: MessageRole;
  content: string;
  provider: string | null;
  model: string | null;
  routing_reason: string | null;
  created_at: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: MessageRead;
}

export interface QuranPlanRead {
  id: string;
  title: string;
  plan_type: "memorization" | "revision";
  surah_start: number;
  ayah_start: number;
  surah_end: number;
  ayah_end: number;
  daily_target_ayahs: number;
  is_active: boolean;
  created_at: string;
}

export interface QuranRevisionItemRead {
  id: string;
  surah: number;
  ayah_start: number;
  ayah_end: number;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  due_at: string;
  last_reviewed_at: string | null;
  last_grade: number | null;
}

export interface QuranAnalytics {
  total_items: number;
  due_today: number;
  average_ease_factor: number;
  reviews_last_7_days: number;
  reviews_last_30_days: number;
  retention_rate_30_days: number | null;
}

export interface BookRead {
  id: string;
  title: string;
  subtitle: string | null;
  author_name: string;
  language: "en" | "ar" | "bilingual";
  created_at: string;
  updated_at: string;
}

export interface ChapterRead {
  id: string;
  order_index: number;
  title: string;
  content_markdown: string;
  updated_at: string;
}

export interface BookWithChapters extends BookRead {
  chapters: ChapterRead[];
}

export interface AdminOverview {
  total_users: number;
  active_users_7d: number;
  total_conversations: number;
  total_messages: number;
  total_books: number;
  total_quran_plans: number;
  messages_by_provider: Record<string, number>;
}

export interface AdminUserRow {
  id: string;
  email: string;
  display_name: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}
