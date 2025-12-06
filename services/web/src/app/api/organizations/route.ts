import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { getUserOrganizations } from "@/lib/org-context";
import prisma from "@/lib/prisma";

// GET /api/organizations - List user's organizations
export async function GET(request: NextRequest) {
  try {
    const session = await auth.api.getSession({ headers: request.headers });
    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = session.user as any;

    // Super admins see all orgs
    let organizations;
    if (user.isSuperAdmin) {
      organizations = await prisma.organization.findMany({
        include: { _count: { select: { members: true } } },
        orderBy: { createdAt: "desc" },
      });
    } else {
      const userOrgs = await getUserOrganizations(session.user.id);
      // Add member count to each organization
      organizations = await Promise.all(
        userOrgs.map(async (org) => {
          const memberCount = await prisma.member.count({
            where: { organizationId: org.id },
          });
          return {
            ...org,
            _count: { members: memberCount },
          };
        })
      );
    }

    return NextResponse.json(organizations);
  } catch (error) {
    console.error("Error fetching organizations:", error);
    return NextResponse.json(
      { error: "Failed to fetch organizations" },
      { status: 500 }
    );
  }
}
