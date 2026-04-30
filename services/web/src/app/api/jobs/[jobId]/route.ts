import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { ragClient } from "@/lib/python-client";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const session = await auth.api.getSession({ headers: request.headers });
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { jobId } = await params;

  try {
    const status = await ragClient.getJobStatus(jobId);
    return NextResponse.json(status);
  } catch {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }
}
