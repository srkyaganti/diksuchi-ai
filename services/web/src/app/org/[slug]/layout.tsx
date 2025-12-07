import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import { isOrgMember, setActiveOrganization } from "@/lib/org-context";
import prisma from "@/lib/prisma";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";

export default async function OrgLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  const user = session.user as any;

  // Get organization by slug
  const org = await prisma.organization.findUnique({
    where: { slug },
  });

  if (!org) {
    redirect("/select-organization");
  }

  // Verify membership (unless super admin)
  if (!user.isSuperAdmin) {
    const isMember = await isOrgMember(session.user.id, org.id);
    if (!isMember) {
      redirect("/select-organization");
    }
  }

  // Set active organization in session if not set or different
  if (session.session?.activeOrganizationId !== org.id) {
    const sessionId = (session as any).session?.id;
    if (sessionId) {
      await setActiveOrganization(sessionId, org.id);
    }
  }

  return (
    <SidebarProvider>
      <AppSidebar organization={org} />
      <SidebarInset>
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
