import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import { getUserRoleInOrg } from "@/lib/org-context";
import { getVisibleChatSessions } from "@/lib/permissions";
import prisma from "@/lib/prisma";
import { ChatHistoryTable } from "@/components/org/chat-history-table";

export const dynamic = "force-dynamic";

export default async function ChatHistoryPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  const user = session.user as any;
  const org = await prisma.organization.findUnique({
    where: { slug },
  });

  if (!org) redirect("/select-organization");

  const role = await getUserRoleInOrg(session.user.id, org.id);
  const chatSessions = await getVisibleChatSessions(
    session.user.id,
    org.id,
    role,
    user.isSuperAdmin
  );

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Chat History</h1>
        <p className="text-muted-foreground">
          {role === "owner" || role === "admin" || user.isSuperAdmin
            ? "View all chat sessions in this organization"
            : "View your chat sessions in this organization"}
        </p>
      </div>

      <ChatHistoryTable
        sessions={chatSessions}
        currentUserId={session.user.id}
        orgSlug={slug}
      />
    </div>
  );
}
