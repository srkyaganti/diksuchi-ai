import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import { getUserRoleInOrg } from "@/lib/org-context";
import prisma from "@/lib/prisma";
import { MemberList } from "@/components/org/member-list";
import { InviteMemberDialog } from "@/components/admin/invite-member-dialog";

export const dynamic = "force-dynamic";

export default async function MembersPage({
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
  const isOwnerOrAdmin =
    user.isSuperAdmin || role === "owner" || role === "admin";

  const members = await prisma.member.findMany({
    where: { organizationId: org.id },
    include: { user: { select: { id: true, name: true, email: true } } },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Members</h1>
          <p className="text-muted-foreground">
            Manage members and their roles in {org.name}
          </p>
        </div>
        {isOwnerOrAdmin && <InviteMemberDialog organizationId={org.id} />}
      </div>

      <MemberList members={members} canManage={isOwnerOrAdmin} />
    </div>
  );
}
