import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { getUserRoleInOrg } from "@/lib/org-context";

/**
 * GET /api/chat/sessions - List user's chat sessions
 */
export async function GET(request: NextRequest) {
  try {
    // Validate session
    const authSession = await auth.api.getSession({
      headers: request.headers,
    });

    if (!authSession) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = authSession.user as any;
    const activeOrgId = authSession.activeOrganizationId;

    // Require active organization for non-super admins
    if (!activeOrgId && !user.isSuperAdmin) {
      return NextResponse.json(
        { error: "No active organization" },
        { status: 400 }
      );
    }

    // Determine role-based filtering
    let whereClause: any = {};

    if (user.isSuperAdmin) {
      // Super admins see all sessions
      whereClause = {};
    } else if (activeOrgId) {
      // Get user's role in the organization
      const role = await getUserRoleInOrg(authSession.user.id, activeOrgId);

      // Owners and admins see all org sessions, members see only their own
      if (role === "owner" || role === "admin") {
        whereClause = { organizationId: activeOrgId };
      } else {
        whereClause = {
          organizationId: activeOrgId,
          userId: authSession.user.id
        };
      }
    }

    const sessions = await prisma.chatSession.findMany({
      where: whereClause,
      include: {
        collection: {
          select: { id: true, name: true },
        },
        messages: {
          orderBy: { createdAt: "desc" },
          take: 1,
        },
      },
      orderBy: { updatedAt: "desc" },
    });

    return NextResponse.json(sessions);
  } catch (error) {
    console.error("Error fetching chat sessions:", error);
    return NextResponse.json(
      { error: "Failed to fetch chat sessions" },
      { status: 500 }
    );
  }
}

/**
 * POST /api/chat/sessions - Create a new chat session
 */
export async function POST(request: NextRequest) {
  try {
    // Validate session
    const authSession = await auth.api.getSession({
      headers: request.headers,
    });

    if (!authSession) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { collectionId, title } = await request.json();

    if (!collectionId) {
      return NextResponse.json(
        { error: "collectionId is required" },
        { status: 400 }
      );
    }

    // Get collection to obtain organizationId
    const collection = await prisma.collection.findUnique({
      where: { id: collectionId },
      select: { organizationId: true },
    });

    if (!collection) {
      return NextResponse.json(
        { error: "Collection not found" },
        { status: 404 }
      );
    }

    const session = await prisma.chatSession.create({
      data: {
        collectionId,
        organizationId: collection.organizationId, // From collection
        userId: authSession.user.id, // Creator for audit trail
        title: title || "New Chat",
      },
    });

    return NextResponse.json(session, { status: 201 });
  } catch (error) {
    console.error("Error creating chat session:", error);
    return NextResponse.json(
      { error: "Failed to create chat session" },
      { status: 500 }
    );
  }
}
