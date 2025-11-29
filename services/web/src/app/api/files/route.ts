import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { randomUUID } from "crypto";
import { existsSync } from "fs";
import { serializeFile } from "@/lib/serializers";
import { submitDocumentProcessing } from "@/lib/python-client";

// POST /api/files - Upload a new file
// Body size limit is configured in next.config.ts
export async function POST(request: NextRequest) {
  try {
    // Validate session
    const session = await auth.api.getSession({
      headers: request.headers,
    });

    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const formData = await request.formData();
    const file = formData.get("file") as File;
    const collectionId = formData.get("collectionId") as string;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    if (!collectionId) {
      return NextResponse.json(
        { error: "Collection ID is required" },
        { status: 400 }
      );
    }

    const user = session.user as any;

    // Verify collection exists and user has permission
    const collection = await prisma.collection.findFirst({
      where: {
        id: collectionId,
      },
    });

    if (!collection) {
      return NextResponse.json(
        { error: "Collection not found" },
        { status: 404 }
      );
    }

    // Check ownership (super admins can upload to any collection)
    if (!user.isSuperAdmin && collection.userId !== session.user.id) {
      return NextResponse.json(
        { error: "Forbidden" },
        { status: 403 }
      );
    }

    // Generate UUID for file storage
    const uuid = randomUUID();
    const fileExtension = file.name.split(".").pop();
    const fileName = `${uuid}.${fileExtension}`;

    // Create uploads directory if it doesn't exist
    const uploadsDir = join(process.cwd(), "uploads");
    if (!existsSync(uploadsDir)) {
      await mkdir(uploadsDir, { recursive: true });
    }

    // Save file to disk
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const filePath = join(uploadsDir, fileName);
    await writeFile(filePath, buffer);

    // Create file record in database
    const fileRecord = await prisma.file.create({
      data: {
        name: file.name,
        uuid: uuid,
        fileSize: BigInt(file.size),
        mimeType: file.type,
        collectionId: collectionId,
        status: "pending",
        ragStatus: "none",
      },
    });

    // Submit document processing to Python worker
    try {
      await submitDocumentProcessing({
        fileId: fileRecord.id,
        collectionId: collectionId,
        fileName: file.name,
        filePath: filePath,
        mimeType: file.type,
      });
      console.log(`Document processing job submitted for file: ${file.name}`);
    } catch (workerError) {
      console.error("Error submitting to Python worker:", workerError);
      // Log error but don't fail the upload - user can retry or process manually
    }

    return NextResponse.json(serializeFile(fileRecord), { status: 201 });
  } catch (error) {
    console.error("Error uploading file:", error);
    return NextResponse.json(
      { error: "Failed to upload file" },
      { status: 500 }
    );
  }
}
