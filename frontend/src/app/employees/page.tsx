import { PrivateShell } from "@/features/dashboard/private-shell";
import { EmployeesList } from "@/features/employees/employees-client";
import { requireSession } from "@/lib/auth/session";
export default async function EmployeesPage() { const session = await requireSession(); return <PrivateShell session={session} serverNow={session.server_now}><EmployeesList /></PrivateShell>; }
