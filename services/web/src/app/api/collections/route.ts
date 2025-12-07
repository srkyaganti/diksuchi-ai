import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { getActiveOrganizationId } from "@/lib/org-context";
import { z } from "zod";

const createCollectionSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
});

// GET /api/collections - List user's collections
export async function GET(request: NextRequest) {
  try {
    // Validate session
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = session.user as any;
    const activeOrgId = await getActiveOrganizationId(session);

    console.log("=== GET /api/collections DEBUG ===");
    console.log("User:", user.email, "| Super Admin:", user.isSuperAdmin);
    console.log("Active Org ID:", activeOrgId);

    // Require active organization for non-super admins
    if (!activeOrgId && !user.isSuperAdmin) {
      return NextResponse.json(
        { error: "No active organization" },
        { status: 400 }
      );
    }

    // Super admins see all collections, regular users see only their org's collections
    const collections = await prisma.collection.findMany({
      where: user.isSuperAdmin ? {} : { organizationId: activeOrgId || undefined },
      include: {
        _count: {
          select: {
            files: true,
          },
        },
      },
      orderBy: {
        createdAt: "desc",
      },
    });

    return NextResponse.json(collections);
  } catch (error) {
    console.error("Error fetching collections:", error);
    return NextResponse.json(
      { error: "Failed to fetch collections" },
      { status: 500 }
    );
  }
}

// POST /api/collections - Create a new collection
export async function POST(request: NextRequest) {
  try {
    // Validate session
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const validation = createCollectionSchema.safeParse(body);

    if (!validation.success) {
      return NextResponse.json(
        { error: "Invalid input", details: validation.error.issues },
        { status: 400 }
      );
    }

    const { name, description } = validation.data;

    const user = session.user as any;
    const activeOrgId = await getActiveOrganizationId(session);

    // Require active organization
    if (!activeOrgId) {
      return NextResponse.json(
        { error: "No active organization" },
        { status: 400 }
      );
    }

    const collection = await prisma.collection.create({
      data: {
        name,
        description,
        organizationId: activeOrgId, // Associate with organization
        userId: session.user.id, // Creator for audit trail
      },
      include: {
        _count: {
          select: {
            files: true,
          },
        },
      },
    });

    return NextResponse.json(collection, { status: 201 });
  } catch (error) {
    console.error("Error creating collection:", error);
    return NextResponse.json(
      { error: "Failed to create collection" },
      { status: 500 }
    );
  }
}
