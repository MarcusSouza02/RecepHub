import { PrivateShell } from "@/features/dashboard/private-shell";
import { CommunicationsClient, type CommunicationContext } from "@/features/communications/communications-client";
import { requireSession } from "@/lib/auth/session";

export default async function CommunicationsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const session = await requireSession(); const query = await searchParams;
  const id = typeof query.schedule_id === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(query.schedule_id) ? query.schedule_id : undefined;
  const kind = query.kind === "revision" || query.kind === "draft" ? query.kind : undefined;
  const number = typeof query.number === "string" && /^[1-9]\d*$/.test(query.number) && Number.isSafeInteger(Number(query.number)) ? Number(query.number) : undefined;
  const context: CommunicationContext = id && kind && number ? { scheduleId: id, sourceKind: kind, sourceNumber: number } : {};
  return <PrivateShell session={session} serverNow={session.server_now}><CommunicationsClient {...context} /></PrivateShell>;
}
