export type VeronicaRole = "user" | "assistant" | "system";

export interface VeronicaAction {
  type: "navigate" | "open_helpline" | "run_sample" | "external_link";
  label: string;
  payload: string;
}

export interface VeronicaMessage {
  id: string;
  role: VeronicaRole;
  content: string;
  timestamp: string;
  actions?: VeronicaAction[];
  suggested_chips?: string[];
  source?: "canned" | "cached" | "gemini" | "fallback" | "guard";
  isError?: boolean;
}

export interface VeronicaChatRequest {
  messages: Array<{
    role: "user" | "assistant" | "system";
    content: string;
  }>;
  language: "en" | "hi";
  session_id?: string;
}

export interface VeronicaChatResponse {
  reply: string;
  language: "en" | "hi";
  source: "canned" | "cached" | "gemini" | "fallback" | "guard";
  actions?: VeronicaAction[];
  suggested_chips?: string[];
}
