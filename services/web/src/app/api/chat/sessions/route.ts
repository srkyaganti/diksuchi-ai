import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";

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

    // Super admins see all sessions, regular users see only their own
    const sessions = await prisma.chatSession.findMany({
      where: user.isSuperAdmin ? {} : { userId: authSession.user.id },
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

    const session = await prisma.chatSession.create({
      data: {
        collectionId,
        userId: authSession.user.id, // Associate with current user
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
