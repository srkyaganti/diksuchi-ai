import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { z } from "zod";

const createOrgSchema = z.object({
  name: z.string().min(1).max(255),
  slug: z.string().min(1).max(255).regex(/^[a-z0-9-]+$/),
});

export async function POST(request: NextRequest) {
  try {
    // Validate session and super admin status
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = session.user as any;
    if (!user.isSuperAdmin) {
      return NextResponse.json(
        { error: "Only super admins can create organizations" },
        { status: 403 }
      );
    }

    // Parse and validate request
    const body = await request.json();
    const { name, slug } = createOrgSchema.parse(body);

    // Check if slug is unique
    const existing = await prisma.organization.findUnique({
      where: { slug },
    });

    if (existing) {
      return NextResponse.json(
        { error: "Organization slug already exists" },
        { status: 409 }
      );
    }

    // Create organization
    const organization = await prisma.organization.create({
      data: {
        id: Math.random().toString(36).substring(7),
        name,
        slug,
        createdAt: new Date(),
      },
    });

    return NextResponse.json(organization, { status: 201 });
  } catch (error) {
    console.error("Create organization error:", error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid request data", details: error.issues },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { error: "Failed to create organization" },
      { status: 500 }
    );
  }
}
