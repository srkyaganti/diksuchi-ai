import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { setActiveOrganization, isOrgMember } from "@/lib/org-context";

// POST /api/organizations/[id]/switch - Set active organization
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: orgId } = await params;
    const session = await auth.api.getSession({ headers: request.headers });
    if (!session) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = session.user as any;

    // Verify membership (super admins can switch to any org)
    if (!user.isSuperAdmin) {
      const isMember = await isOrgMember(session.user.id, orgId);
      if (!isMember) {
        return NextResponse.json(
          { error: "Not a member of this organization" },
          { status: 403 }
        );
      }
    }

    // Get session ID from the session object
    console.log("=== SWITCH ORGANIZATION DEBUG ===");
    console.log("Session object:", JSON.stringify(session, null, 2));

    const sessionId = (session as any).session?.id;
    console.log("Extracted session ID:", sessionId);

    if (!sessionId) {
      return NextResponse.json(
        { error: "No session ID found" },
        { status: 401 }
      );
    }

    await setActiveOrganization(sessionId, orgId);
    console.log("Successfully switched to organization:", orgId);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error switching organization:", error);
    return NextResponse.json(
      { error: "Failed to switch organization" },
      { status: 500 }
    );
  }
}
