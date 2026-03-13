import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { readFile } from "fs/promises";
import { join } from "path";
import { existsSync } from "fs";

const STORAGE_PATH =
  process.env.DOCLING_STORAGE_PATH || join(process.cwd(), "storage");

const MIME_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".bmp": "image/bmp",
};

function getMimeType(filename: string): string {
  const ext = filename.substring(filename.lastIndexOf(".")).toLowerCase();
  return MIME_TYPES[ext] || "application/octet-stream";
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; filename: string }> },
) {
  try {
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id, filename } = await params;

    if (
      filename.includes("..") ||
      filename.includes("/") ||
      filename.includes("\\")
    ) {
      return NextResponse.json({ error: "Invalid filename" }, { status: 400 });
    }

    const file = await prisma.file.findUnique({
      where: { id },
      include: { collection: true },
    });

    if (!file) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    const user = session.user as any;
    if (
      !user.isSuperAdmin &&
      file.collection.organizationId !==
        session.session?.activeOrganizationId
    ) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    const imagePath = join(STORAGE_PATH, file.uuid, "images", filename);

    if (!existsSync(imagePath)) {
      return NextResponse.json(
        { error: "Image not found" },
        { status: 404 },
      );
    }

    const buffer = await readFile(imagePath);
    const contentType = getMimeType(filename);

    return new NextResponse(buffer, {
      headers: {
        "Content-Type": contentType,
        "Content-Length": buffer.length.toString(),
        "Cache-Control": "public, max-age=31536000, immutable",
      },
    });
  } catch (error) {
    console.error("Error serving image:", error);
    return NextResponse.json(
      { error: "Failed to serve image" },
      { status: 500 },
    );
  }
}
