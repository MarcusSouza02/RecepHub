import { PrivateShell } from "@/features/dashboard/private-shell";
import { AbsenceRecord } from "@/features/absences/absences-client";
import { requireSession } from "@/lib/auth/session";
export default async function AbsencePage({ params }: { params: Promise<{ id: string }> }) { const session = await requireSession(); const { id } = await params; return <PrivateShell session={session} serverNow={session.server_now}><AbsenceRecord id={id} /></PrivateShell>; }
