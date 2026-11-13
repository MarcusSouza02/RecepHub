import { PrivateShell } from "@/features/dashboard/private-shell";
import { UnitRecord } from "@/features/units/units-client";
import { requireSession } from "@/lib/auth/session";
export default async function NewUnitPage() {
  const session = await requireSession();
  return <PrivateShell session={session} serverNow={session.server_now}><UnitRecord /></PrivateShell>;
}
