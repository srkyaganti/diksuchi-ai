import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { serializeFiles } from "@/lib/serializers";

// GET /api/collections/[id]/files - Get all files in a collection
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    // Validate session
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;
    const user = session.user as any;

    // Verify collection exists
    const collection = await prisma.collection.findFirst({
      where: {
        id,
      },
    });

    if (!collection) {
      return NextResponse.json(
        { error: "Collection not found" },
        { status: 404 }
      );
    }

    // Check ownership (super admins can access any collection)
    if (!user.isSuperAdmin && collection.userId !== session.user.id) {
      return NextResponse.json(
        { error: "Forbidden" },
        { status: 403 }
      );
    }

    const { searchParams } = new URL(request.url);
    const onlyCompleted = searchParams.get("onlyCompleted") === "true";

    const files = await prisma.file.findMany({
      where: {
        collectionId: id,
        ...(onlyCompleted && { ragStatus: "completed" }),
      },
      orderBy: {
        uploadedAt: "desc",
      },
    });

    return NextResponse.json(serializeFiles(files));
  } catch (error) {
    console.error("Error fetching files:", error);
    return NextResponse.json(
      { error: "Failed to fetch files" },
      { status: 500 }
    );
  }
}
