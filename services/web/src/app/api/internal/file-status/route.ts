/**
 * Internal API endpoint for Python worker to update file processing status.
 * This endpoint is called by the Python worker as a callback after processing stages.
 */

import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export const dynamic = "force-dynamic";

interface FileStatusUpdate {
  fileId: string;
  ragStatus: "none" | "processing" | "completed" | "failed";
  ragError?: string;
  processedAt?: string;
}

export async function POST(req: NextRequest) {
  try {
    // Validate API secret for internal calls
    const apiSecret = req.headers.get("x-api-secret");
    const expectedSecret = process.env.INTERNAL_API_SECRET;

    if (expectedSecret && apiSecret !== expectedSecret) {
      return NextResponse.json(
        { error: "Unauthorized: Invalid API secret" },
        { status: 401 }
      );
    }

    // Parse request body
    const body: FileStatusUpdate = await req.json();
    const { fileId, ragStatus, ragError, processedAt } = body;

    // Validate required fields
    if (!fileId || !ragStatus) {
      return NextResponse.json(
        { error: "Missing required fields: fileId and ragStatus" },
        { status: 400 }
      );
    }

    // Validate ragStatus value
    const validStatuses = ["none", "processing", "completed", "failed"];
    if (!validStatuses.includes(ragStatus)) {
      return NextResponse.json(
        { error: `Invalid ragStatus. Must be one of: ${validStatuses.join(", ")}` },
        { status: 400 }
      );
    }

    // Prepare update data
    const updateData: any = {
      ragStatus,
      updatedAt: new Date(),
    };

    // Add optional fields
    if (ragError !== undefined) {
      updateData.ragError = ragError;
    }

    if (processedAt) {
      updateData.processedAt = new Date(processedAt);
    }

    // Clear error when transitioning to processing or completed
    if (ragStatus === "processing" || ragStatus === "completed") {
      updateData.ragError = null;
    }

    // Update file record in database
    const updatedFile = await prisma.file.update({
      where: { id: fileId },
      data: updateData,
    });

    console.log(
      `[File Status Update] File ${fileId}: ${ragStatus}`,
      ragError ? `Error: ${ragError}` : ""
    );

    return NextResponse.json({
      success: true,
      file: {
        id: updatedFile.id,
        ragStatus: updatedFile.ragStatus,
        processedAt: updatedFile.processedAt,
      },
    });
  } catch (error: any) {
    console.error("[File Status Update] Error:", error);

    // Handle file not found
    if (error.code === "P2025") {
      return NextResponse.json(
        { error: "File not found" },
        { status: 404 }
      );
    }

    // Generic error response
    return NextResponse.json(
      { error: "Failed to update file status", details: error.message },
      { status: 500 }
    );
  }
}

// Optional: GET endpoint to check status (for debugging)
export async function GET(req: NextRequest) {
  const fileId = req.nextUrl.searchParams.get("fileId");

  if (!fileId) {
    return NextResponse.json(
      { error: "Missing fileId parameter" },
      { status: 400 }
    );
  }

  try {
    const file = await prisma.file.findUnique({
      where: { id: fileId },
      select: {
        id: true,
        name: true,
        ragStatus: true,
        ragError: true,
        processedAt: true,
        updatedAt: true,
      },
    });

    if (!file) {
      return NextResponse.json(
        { error: "File not found" },
        { status: 404 }
      );
    }

    return NextResponse.json({ file });
  } catch (error: any) {
    console.error("[File Status Check] Error:", error);
    return NextResponse.json(
      { error: "Failed to fetch file status", details: error.message },
      { status: 500 }
    );
  }
}
