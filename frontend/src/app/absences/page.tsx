import { PrivateShell } from "@/features/dashboard/private-shell";
import { AbsencesList } from "@/features/absences/absences-client";
import { requireSession } from "@/lib/auth/session";
export default async function AbsencesPage() { const session = await requireSession(); return <PrivateShell session={session} serverNow={session.server_now}><AbsencesList /></PrivateShell>; }
