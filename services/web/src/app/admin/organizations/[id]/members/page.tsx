import { notFound } from "next/navigation";
import prisma from "@/lib/prisma";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InviteMemberDialog } from "@/components/admin/invite-member-dialog";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function OrganizationMembersPage({ params }: PageProps) {
  const { id } = await params;

  const organization = await prisma.organization.findUnique({
    where: { id },
    include: {
      members: {
        include: {
          user: true,
        },
      },
    },
  });

  if (!organization) {
    notFound();
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{organization.name}</h1>
          <p className="text-muted-foreground">Manage organization members</p>
        </div>
        <InviteMemberDialog organizationId={organization.id} />
      </div>

      <div className="grid gap-4">
        {organization.members.map((member) => (
          <Card key={member.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{member.user.name || "Unnamed User"}</CardTitle>
                  <CardDescription>{member.user.email}</CardDescription>
                </div>
                <Badge>{member.role}</Badge>
              </div>
            </CardHeader>
          </Card>
        ))}

        {organization.members.length === 0 && (
          <Card>
            <CardContent className="flex min-h-[200px] items-center justify-center">
              <div className="text-center">
                <p className="text-muted-foreground">No members yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Invite members to get started
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
