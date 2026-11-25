export type Assignment = { id: string; unit_id: string; unit_name: string; start_time: string; end_time: string; break_start_time: string | null; break_end_time: string | null; position: string | null };
export type ScheduleDay = { id: string; employee_id: string; employee_name: string; work_date: string; state: "pending" | "working" | "non_working" | "excluded"; resolution_note: string | null; source_data?: { state?: string; start_time?: string | null; end_time?: string | null; break_start_time?: string | null; break_end_time?: string | null; home_unit_active?: boolean | null; home_unit_id?: string | null }; assignments: Assignment[] };
export type Diagnostics = { errors: { code: string; message: string }[]; warnings: { code: string; message: string }[] };
export type ScheduleSummary = { id: string; week_start: string; status: string; version: number; latest_revision_number: number | null };
export type Schedule = ScheduleSummary & { days: ScheduleDay[]; diagnostics: Diagnostics };
export type Revision = { id: string; number: number; source_version: number; published_at: string; snapshot: Schedule };
export type Unit = { id: string; name: string; active: boolean };
