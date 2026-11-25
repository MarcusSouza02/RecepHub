import { PrivateShell } from "@/features/dashboard/private-shell";
import { ScheduleDetail } from "@/features/schedules/schedules-client";
import { requireSession } from "@/lib/auth/session";
export default async function Page({ params }: { params: Promise<{ id: string }> }) { const session = await requireSession(); const { id } = await params; return <PrivateShell session={session} serverNow={session.server_now}><ScheduleDetail id={id} /></PrivateShell>; }
