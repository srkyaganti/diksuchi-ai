import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { readFile } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

// GET /api/files/[id]/download - Download a file
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

    const file = await prisma.file.findUnique({
      where: { id },
      include: {
        collection: true,
      },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    // Check ownership (super admins can download any file)
    if (!user.isSuperAdmin && file.collection.userId !== session.user.id) {
      return NextResponse.json(
        { error: "Forbidden" },
        { status: 403 }
      );
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

    // Return file with appropriate headers
    return new NextResponse(buffer, {
      headers: {
        "Content-Type": file.mimeType,
        "Content-Disposition": `attachment; filename="${file.name}"`,
        "Content-Length": file.fileSize.toString(),
      },
    });
  } catch (error) {
    console.error("Error downloading file:", error);
    return NextResponse.json(
      { error: "Failed to download file" },
      { status: 500 }
    );
  }
}
