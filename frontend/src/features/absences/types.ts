export type AbsenceType = "vacation" | "day_off" | "compensation" | "other";
export type Absence = {
  id: string; employee_id: string; employee_name: string; type: AbsenceType;
  mode: "full_day" | "partial"; start_date: string; end_date: string;
  start_time: string | null; end_time: string | null; notes: string | null;
  status: "active" | "cancelled"; version: number; created_at: string; updated_at: string;
  cancelled_at: string | null; overlap_warning: boolean; overlap_ids: string[];
};
export type AbsencePage = { items: Absence[]; total: number; page: number; page_size: number };
export type AbsenceEvent = { id: string; absence_id: string; version: number; action: "created" | "updated" | "cancelled"; snapshot: Absence; created_at: string };
