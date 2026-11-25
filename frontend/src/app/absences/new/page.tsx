import { PrivateShell } from "@/features/dashboard/private-shell";
import { AbsenceRecord } from "@/features/absences/absences-client";
import { requireSession } from "@/lib/auth/session";
export default async function NewAbsencePage() { const session = await requireSession(); return <PrivateShell session={session} serverNow={session.server_now}><AbsenceRecord /></PrivateShell>; }
