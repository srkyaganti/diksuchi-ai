import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { z } from "zod";

const changePasswordSchema = z.object({
  currentPassword: z.string(),
  newPassword: z.string().min(8),
  revokeOtherSessions: z.boolean().optional(),
});

export async function POST(request: NextRequest) {
  try {
    // Validate session
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse and validate request
    const body = await request.json();
    const { currentPassword, newPassword, revokeOtherSessions } = changePasswordSchema.parse(body);

    // Call Better Auth's change password endpoint (proper password hashing)
    const baseURL = process.env.BETTER_AUTH_URL || "http://localhost:3000";
    const changePasswordResponse = await fetch(`${baseURL}/api/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Forward cookies for authentication
        "Cookie": request.headers.get("cookie") || "",
        // Forward origin header for Better Auth's origin check
        "Origin": request.headers.get("origin") || baseURL,
        // Forward other important headers
        "User-Agent": request.headers.get("user-agent") || "internal",
      },
      body: JSON.stringify({
        currentPassword,
        newPassword,
        revokeOtherSessions: revokeOtherSessions || false,
      }),
    });

    if (!changePasswordResponse.ok) {
      const error = await changePasswordResponse.json();
      return NextResponse.json(
        { error: error.message || "Failed to change password" },
        { status: changePasswordResponse.status }
      );
    }

    // Clear mustChangePassword flag after successful password change
    await prisma.user.update({
      where: { id: session.user.id },
      data: {
        mustChangePassword: false,
      },
    });

    const result = await changePasswordResponse.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error("Change password error:", error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid request data" },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { error: "Failed to change password" },
      { status: 500 }
    );
  }
}
