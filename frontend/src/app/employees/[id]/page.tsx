import { PrivateShell } from "@/features/dashboard/private-shell";
import { EmployeeRecord } from "@/features/employees/employees-client";
import { requireSession } from "@/lib/auth/session";
export default async function EmployeePage({ params }: { params: Promise<{ id: string }> }) { const session = await requireSession(); const { id } = await params; return <PrivateShell session={session} serverNow={session.server_now}><EmployeeRecord id={id} /></PrivateShell>; }
