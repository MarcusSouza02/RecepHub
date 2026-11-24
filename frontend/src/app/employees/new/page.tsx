import { PrivateShell } from "@/features/dashboard/private-shell";
import { EmployeeRecord } from "@/features/employees/employees-client";
import { requireSession } from "@/lib/auth/session";
export default async function NewEmployeePage() { const session = await requireSession(); return <PrivateShell session={session} serverNow={session.server_now}><EmployeeRecord /></PrivateShell>; }
