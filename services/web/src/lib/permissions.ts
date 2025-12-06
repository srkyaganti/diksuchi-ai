import prisma from "@/lib/prisma";
import { isOrgMember, getUserRoleInOrg } from "./org-context";
import { ChatSession } from "@/generated/prisma/client";

/**
 * Require that a user is a member of an organization
 * Throws an error if the user is not a member (unless super admin)
 */
export async function requireOrgMembership(
  userId: string,
  orgId: string,
  isSuperAdmin: boolean = false
): Promise<void> {
  if (isSuperAdmin) return; // Super admins bypass

  const isMember = await isOrgMember(userId, orgId);
  if (!isMember) {
    throw new Error("Not a member of this organization");
  }
}

/**
 * Require that a user has one of the specified roles in an organization
 * Throws an error if the user doesn't have the required role (unless super admin)
 */
export async function requireOrgRole(
  userId: string,
  orgId: string,
  allowedRoles: string[],
  isSuperAdmin: boolean = false
): Promise<void> {
  if (isSuperAdmin) return; // Super admins bypass

  const role = await getUserRoleInOrg(userId, orgId);
  if (!role || !allowedRoles.includes(role)) {
    throw new Error("Insufficient permissions");
  }
}

/**
 * Get visible chat sessions for a user in an organization
 * Role-based visibility:
 * - Owners and admins see all organization chats
 * - Members see only their own chats
 * - Super admins see all chats
 */
export async function getVisibleChatSessions(
  userId: string,
  orgId: string,
  role: string | null,
  isSuperAdmin: boolean = false
): Promise<
  Array<
    ChatSession & {
      user: { id: string; name: string; email: string };
      collection: { id: string; name: string };
    }
  >
> {
  // Owners and admins see all org chats
  if (isSuperAdmin || role === "owner" || role === "admin") {
    return await prisma.chatSession.findMany({
      where: { organizationId: orgId },
      include: {
        user: { select: { id: true, name: true, email: true } },
        collection: { select: { id: true, name: true } },
      },
      orderBy: { updatedAt: "desc" },
    });
  }

  // Members see only their own chats
  return await prisma.chatSession.findMany({
    where: { organizationId: orgId, userId },
    include: {
      user: { select: { id: true, name: true, email: true } },
      collection: { select: { id: true, name: true } },
    },
    orderBy: { updatedAt: "desc" },
  });
}

/**
 * Check if a user can manage members (invite, remove, etc.)
 * Only owners and admins can manage members (plus super admins)
 */
export function canManageMembers(
  role: string | null,
  isSuperAdmin: boolean = false
): boolean {
  return isSuperAdmin || role === "owner" || role === "admin";
}
