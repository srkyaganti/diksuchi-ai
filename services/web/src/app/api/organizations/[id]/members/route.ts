import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { requireOrgRole } from "@/lib/permissions";

// GET /api/organizations/[id]/members - List org members (owners/admins only)
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const session = await auth.api.getSession({ headers: request.headers });
    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = session.user as any;

    // Try to find by ID first, then by slug
    let org = await prisma.organization.findUnique({ where: { id } });
    if (!org) {
      org = await prisma.organization.findUnique({ where: { slug: id } });
    }

    if (!org) {
      return NextResponse.json(
        { error: "Organization not found" },
        { status: 404 }
      );
    }

    // Only owners/admins can view members
    try {
      await requireOrgRole(
        session.user.id,
        org.id,
        ["owner", "admin"],
        user.isSuperAdmin
      );
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 403 });
    }

    const members = await prisma.member.findMany({
      where: { organizationId: org.id },
      include: { user: { select: { id: true, name: true, email: true } } },
      orderBy: { createdAt: "desc" },
    });

    return NextResponse.json(members);
  } catch (error) {
    console.error("Error fetching members:", error);
    return NextResponse.json(
      { error: "Failed to fetch members" },
      { status: 500 }
    );
  }
}
