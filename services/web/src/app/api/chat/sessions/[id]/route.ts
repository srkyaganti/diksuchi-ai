import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    // Validate session
    const authSession = await auth.api.getSession({
      headers: request.headers,
    });

    if (!authSession) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const user = authSession.user as any;

    const session = await prisma.chatSession.findUnique({
      where: { id },
      include: {
        messages: {
          select: {
            id: true,
            role: true,
            content: true,
            parts: true,
            sources: true,
            createdAt: true,
          },
          orderBy: { createdAt: "asc" },
        },
        collection: {
          select: { id: true, name: true },
        },
      },
    });

    if (!session) {
      return NextResponse.json(
        { error: "Chat session not found" },
        { status: 404 }
      );
    }

    // Check ownership (super admins can access any session)
    if (!user.isSuperAdmin && session.userId !== authSession.user.id) {
      return NextResponse.json(
        { error: "Forbidden" },
        { status: 403 }
      );
    }

    return NextResponse.json(session);
  } catch (error) {
    console.error("Error fetching chat session:", error);
    return NextResponse.json(
      { error: "Failed to fetch chat session" },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    // Validate session
    const authSession = await auth.api.getSession({
      headers: request.headers,
    });

    if (!authSession) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const user = authSession.user as any;

    // Verify session exists and check ownership
    const session = await prisma.chatSession.findUnique({
      where: { id },
    });

    if (!session) {
      return NextResponse.json(
        { error: "Chat session not found" },
        { status: 404 }
      );
    }

    // Check ownership (super admins can delete any session)
    if (!user.isSuperAdmin && session.userId !== authSession.user.id) {
      return NextResponse.json(
        { error: "Forbidden" },
        { status: 403 }
      );
    }

    // Delete session (cascade will delete messages)
    await prisma.chatSession.delete({
      where: { id },
    });

    return NextResponse.json({ message: "Chat session deleted" });
  } catch (error) {
    console.error("Error deleting chat session:", error);
    return NextResponse.json(
      { error: "Failed to delete chat session" },
      { status: 500 }
    );
  }
}
