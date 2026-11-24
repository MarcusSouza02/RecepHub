import { PrivateShell } from "@/features/dashboard/private-shell";
import { UnitRecord } from "@/features/units/units-client";
import { requireSession } from "@/lib/auth/session";
export default async function UnitPage({ params }: { params: Promise<{ id: string }> }) {
  const session = await requireSession();
  const { id } = await params;
  return <PrivateShell session={session} serverNow={session.server_now}><UnitRecord key={id} id={id} /></PrivateShell>;
}
