export type DayState = "pending" | "working" | "non_working";
export type TimeField = "start_time" | "end_time" | "break_start_time" | "break_end_time";
export type PatternDay = { weekday: number; state: DayState } & Record<TimeField, string | null>;
export type WeeklyPattern = {
  employee_id: string;
  days: (PatternDay & { duration_minutes: number | null; is_complete: boolean })[];
  subtotal_minutes: number;
  total_minutes: number | null;
  is_complete: boolean;
};
export const dayNames = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"];
export const timeFields: { key: TimeField; label: string }[] = [
  { key: "start_time", label: "Entrada" }, { key: "end_time", label: "Saída" },
  { key: "break_start_time", label: "Início do intervalo" }, { key: "break_end_time", label: "Fim do intervalo" },
];
export function editableDay(day: PatternDay): PatternDay {
  return { weekday: day.weekday, state: day.state, start_time: day.start_time?.slice(0, 5) || null,
    end_time: day.end_time?.slice(0, 5) || null, break_start_time: day.break_start_time?.slice(0, 5) || null,
    break_end_time: day.break_end_time?.slice(0, 5) || null };
}
export function dayError(day: PatternDay): string | null {
  if (day.state !== "working") return null;
  const { start_time: start, end_time: end, break_start_time: pause, break_end_time: resume } = day;
  if (start && end && start >= end) return "A saída deve ser posterior à entrada, no mesmo dia.";
  if (pause && resume && pause >= resume) return "O fim do intervalo deve ser posterior ao início.";
  if ([pause, resume].some(value => value && ((start && value < start) || (end && value > end)))) return "O intervalo deve estar contido na jornada.";
  return null;
}
export function duration(day: PatternDay): number | null {
  if (day.state === "non_working") return 0;
  if (day.state === "pending" || dayError(day) || !day.start_time || !day.end_time || Boolean(day.break_start_time) !== Boolean(day.break_end_time)) return null;
  const minutes = (value: string) => Number(value.slice(0, 2)) * 60 + Number(value.slice(3, 5));
  return minutes(day.end_time) - minutes(day.start_time) - (day.break_start_time && day.break_end_time ? minutes(day.break_end_time) - minutes(day.break_start_time) : 0);
}
export function hours(minutes: number): string { return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, "0")}min`; }
