import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { hash } from "bcryptjs";
import { z } from "zod";

const changePasswordSchema = z.object({
  newPassword: z.string().min(8),
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
    const { newPassword } = changePasswordSchema.parse(body);

    // Hash new password
    const hashedPassword = await hash(newPassword, 10);

    // Update user password in the account table and clear mustChangePassword flag
    await prisma.$transaction([
      // Update password in account table
      prisma.account.updateMany({
        where: {
          userId: session.user.id,
          providerId: "credential",
        },
        data: {
          password: hashedPassword,
        },
      }),
      // Clear mustChangePassword flag in user table
      prisma.user.update({
        where: { id: session.user.id },
        data: {
          mustChangePassword: false,
        },
      }),
    ]);

    return NextResponse.json({ success: true });
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
