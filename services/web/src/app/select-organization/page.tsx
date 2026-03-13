import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { OrganizationCard } from "@/components/org/organization-card";
import { CreateOrganizationDialog } from "@/components/admin/create-organization-dialog";
import { BrandHeader, BrandFooter } from "@/components/brand-header";

export const dynamic = "force-dynamic";

export default async function SelectOrganizationPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string }>;
}) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  const user = session.user as any;
  const { redirect: redirectPath } = await searchParams;

  // Debug logging
  console.log("=== SELECT ORGANIZATION PAGE DEBUG ===");
  console.log("User:", JSON.stringify(user, null, 2));
  console.log("Is Super Admin:", user.isSuperAdmin);
  console.log("Session:", JSON.stringify(session, null, 2));

  // Get user's organizations
  let organizations;
  if (user.isSuperAdmin) {
    // Super admins see all orgs
    organizations = await prisma.organization.findMany({
      include: {
        members: { where: { userId: session.user.id } },
        _count: { select: { members: true } },
      },
      orderBy: { createdAt: "desc" },
    });
  } else {
    const members = await prisma.member.findMany({
      where: { userId: session.user.id },
      include: {
        organization: {
          include: { _count: { select: { members: true } } },
        },
      },
    });
    organizations = members.map((m) => ({
      ...m.organization,
      members: [m], // Include user's membership for role display
    }));
  }

  if (organizations.length === 0) {
    console.log("=== NO ORGANIZATIONS FOUND ===");
    console.log("Rendering empty state");
    console.log("user.isSuperAdmin:", user.isSuperAdmin);
    console.log("Will show CreateOrganizationDialog:", !!user.isSuperAdmin);

    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-4">
        <BrandHeader variant="compact" />
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">No Organizations</h1>
          <p className="text-muted-foreground mb-6">
            {user.isSuperAdmin
              ? "Start by creating a new organization to get started."
              : "You are not a member of any organizations. Please contact your administrator."}
          </p>
          {user.isSuperAdmin && <CreateOrganizationDialog />}
        </div>
        <BrandFooter />
      </div>
    );
  }

  const redirectTo = redirectPath || "chat";

  return (
    <div className="container mx-auto min-h-screen flex flex-col py-10 px-4">
      <BrandHeader variant="compact" className="mb-8" />
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Select Organization</h1>
        {user.isSuperAdmin && <CreateOrganizationDialog />}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 flex-1">
        {organizations.map((org) => (
          <OrganizationCard
            key={org.id}
            organization={org}
            userRole={org.members?.[0]?.role}
            redirectPath={redirectTo}
          />
        ))}
      </div>
      <BrandFooter className="mt-12" />
    </div>
  );
}
