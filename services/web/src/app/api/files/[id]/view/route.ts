import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { getActiveOrganizationId } from "@/lib/org-context";
import { readFile } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

// GET /api/files/[id]/view - View a file inline (for PDF viewer)
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
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
      include: { collection: true },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    // Check organization access (super admins can view any file)
    if (
      !user.isSuperAdmin &&
      file.collection.organizationId !== activeOrgId
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // Read file from disk
    const fileExtension = file.name.split(".").pop();
    const fileName = `${file.uuid}.${fileExtension}`;
    const filePath = join(process.cwd(), "uploads", fileName);

    if (!existsSync(filePath)) {
      return NextResponse.json(
        { error: "File not found on disk" },
        { status: 404 }
      );
    }

    const buffer = await readFile(filePath);

    // Return file inline so the browser renders it (not downloads)
    return new NextResponse(buffer, {
      headers: {
        "Content-Type": file.mimeType,
        "Content-Disposition": `inline; filename="${file.name}"`,
        "Content-Length": file.fileSize.toString(),
        "Cache-Control": "private, max-age=3600",
      },
    });
  } catch (error) {
    console.error("Error viewing file:", error);
    return NextResponse.json(
      { error: "Failed to view file" },
      { status: 500 }
    );
  }
}
