import { PrivateShell } from "@/features/dashboard/private-shell";
import { UnitsList } from "@/features/units/units-client";
import { requireSession } from "@/lib/auth/session";
export default async function UnitsPage() {
  const session = await requireSession();
  return <PrivateShell session={session} serverNow={session.server_now}><UnitsList /></PrivateShell>;
}
