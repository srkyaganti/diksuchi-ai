import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { hash } from "bcryptjs";
import { z } from "zod";
import { randomBytes } from "crypto";

const inviteMemberSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
  role: z.enum(["owner", "admin", "member"]),
  organizationId: z.string(),
});

// Generate secure random password
function generateSecurePassword(length: number = 16): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%^&*";
  const bytes = randomBytes(length);
  let password = "";

  for (let i = 0; i < length; i++) {
    password += chars[bytes[i] % chars.length];
  }

  return password;
}

export async function POST(request: NextRequest) {
  try {
    // Validate session and admin status
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const currentUser = session.user as any;

    // Check if user is super admin or organization admin
    const body = await request.json();
    const { email, name, role, organizationId } = inviteMemberSchema.parse(body);

    // Verify organization exists
    const organization = await prisma.organization.findUnique({
      where: { id: organizationId },
      include: {
        members: {
          where: { userId: currentUser.id },
        },
      },
    });

    if (!organization) {
      return NextResponse.json(
        { error: "Organization not found" },
        { status: 404 }
      );
    }

    // Check permissions: must be super admin OR organization owner/admin
    const isOrgAdmin = organization.members.some(
      (member) => member.role === "owner" || member.role === "admin"
    );

    if (!currentUser.isSuperAdmin && !isOrgAdmin) {
      return NextResponse.json(
        { error: "Insufficient permissions" },
        { status: 403 }
      );
    }

    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email },
    });

    if (existingUser) {
      // Check if already a member of this organization
      const existingMember = await prisma.member.findFirst({
        where: {
          userId: existingUser.id,
          organizationId,
        },
      });

      if (existingMember) {
        return NextResponse.json(
          { error: "User is already a member of this organization" },
          { status: 409 }
        );
      }

      // Add existing user to organization
      await prisma.member.create({
        data: {
          id: Math.random().toString(36).substring(7),
          userId: existingUser.id,
          organizationId,
          role,
          createdAt: new Date(),
        },
      });

      return NextResponse.json({
        message: "Existing user added to organization",
        userId: existingUser.id,
      });
    }

    // Generate random password
    const temporaryPassword = generateSecurePassword();
    const hashedPassword = await hash(temporaryPassword, 10);

    // Create new user with mustChangePassword flag
    const newUser = await prisma.user.create({
      data: {
        id: Math.random().toString(36).substring(7),
        email,
        name,
        emailVerified: true, // Auto-verify in offline environment
        mustChangePassword: true,
        createdAt: new Date(),
        updatedAt: new Date(),
        accounts: {
          create: {
            id: Math.random().toString(36).substring(7),
            accountId: email,
            providerId: "credential",
            password: hashedPassword,
            createdAt: new Date(),
            updatedAt: new Date(),
          },
        },
        members: {
          create: {
            id: Math.random().toString(36).substring(7),
            organizationId,
            role,
            createdAt: new Date(),
          },
        },
      },
    });

    return NextResponse.json({
      userId: newUser.id,
      password: temporaryPassword, // Return plain password for admin to share
    }, { status: 201 });

  } catch (error) {
    console.error("Invite member error:", error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid request data", details: error.issues },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { error: "Failed to invite member" },
      { status: 500 }
    );
  }
}
