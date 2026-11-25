import { PrivateShell } from "@/features/dashboard/private-shell";
import { SchedulesList } from "@/features/schedules/schedules-client";
import { requireSession } from "@/lib/auth/session";
export default async function Page() { const session = await requireSession(); return <PrivateShell session={session} serverNow={session.server_now}><SchedulesList /></PrivateShell>; }
