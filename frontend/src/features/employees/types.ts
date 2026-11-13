export type Employee = { id: string; display_name: string; home_unit_id: string | null; home_unit_name: string | null; home_unit_active: boolean | null; notes: string | null; active: boolean };
export type EmployeePage = { items: Employee[]; total: number; page: number; page_size: number };
export type UnitOption = { id: string; name: string; active: boolean };
