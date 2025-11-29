import prisma from "@/lib/prisma";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CreateOrganizationDialog } from "@/components/admin/create-organization-dialog";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function OrganizationsPage() {
  const organizations = await prisma.organization.findMany({
    include: {
      members: {
        include: {
          user: true,
        },
      },
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Organizations</h1>
          <p className="text-muted-foreground">Create and manage organizations</p>
        </div>
        <CreateOrganizationDialog />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {organizations.map((org) => (
          <Link key={org.id} href={`/admin/organizations/${org.id}/members`}>
            <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
              <CardHeader>
                <CardTitle>{org.name}</CardTitle>
                <CardDescription>{org.slug}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  <p className="text-muted-foreground">
                    Members: {org.members.length}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Created: {new Date(org.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}

        {organizations.length === 0 && (
          <div className="col-span-full flex min-h-[400px] items-center justify-center rounded-lg border border-dashed">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="rounded-full bg-muted p-4">
                <svg className="h-10 w-10 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div className="max-w-md">
                <h3 className="text-lg font-semibold">No organizations yet</h3>
                <p className="text-sm text-muted-foreground mt-2">
                  Get started by creating your first organization
                </p>
              </div>
              <CreateOrganizationDialog />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
