import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { getActiveOrganizationId } from "@/lib/org-context";
import { unlink } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";
import { serializeFile } from "@/lib/serializers";
import { deleteDocumentFromRAG } from "@/lib/python-client";

// GET /api/files/[id] - Get file details
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
    const activeOrgId = await getActiveOrganizationId(session);

    const file = await prisma.file.findUnique({
      where: { id },
      include: {
        collection: true,
      },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    // Check organization access (super admins can access any file)
    if (
      !user.isSuperAdmin &&
      file.collection.organizationId !== activeOrgId
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    return NextResponse.json(serializeFile(file));
  } catch (error) {
    console.error("Error fetching file:", error);
    return NextResponse.json(
      { error: "Failed to fetch file" },
      { status: 500 }
    );
  }
}

// DELETE /api/files/[id] - Delete a file
export async function DELETE(
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
    const activeOrgId = await getActiveOrganizationId(session);

    const file = await prisma.file.findUnique({
      where: { id },
      include: {
        collection: true,
      },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    // Check organization access (super admins can delete any file)
    if (
      !user.isSuperAdmin &&
      file.collection.organizationId !== activeOrgId
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Clean up RAG indices BEFORE removing the file/DB row so a failure here
    // doesn't leave orphan embeddings referenced by chat retrieval.
    try {
      await deleteDocumentFromRAG(file.collectionId, file.uuid);
    } catch (ragError) {
      console.error("Failed to clean up RAG indices:", ragError);
      return NextResponse.json(
        {
          error:
            "Could not remove document from the indexing service. The file was not deleted. Please retry.",
          detail:
            ragError instanceof Error ? ragError.message : String(ragError),
        },
        { status: 502 }
      );
    }

    // Delete physical file
    const fileExtension = file.name.split(".").pop();
    const fileName = `${file.uuid}.${fileExtension}`;
    const filePath = join(process.cwd(), "uploads", fileName);

    if (existsSync(filePath)) {
      await unlink(filePath);
    }

    // Delete database record
    await prisma.file.delete({
      where: { id },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting file:", error);
    return NextResponse.json(
      { error: "Failed to delete file" },
      { status: 500 }
    );
  }
}
