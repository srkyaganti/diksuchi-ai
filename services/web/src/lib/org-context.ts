import prisma from "@/lib/prisma";
import { Organization } from "@/generated/prisma/client";

/**
 * Get all organizations a user belongs to
 */
export async function getUserOrganizations(userId: string): Promise<Organization[]> {
  const members = await prisma.member.findMany({
    where: { userId },
    include: { organization: true },
    orderBy: { createdAt: "desc" },
  });
  return members.map((m) => m.organization);
}

/**
 * Get the active organization ID from a Better Auth session
 * Better Auth doesn't expose custom session fields, so we read from DB
 */
export async function getActiveOrganizationId(session: any): Promise<string | null> {
  const sessionId = session?.session?.id;
  if (!sessionId) return null;

  const dbSession = await prisma.session.findUnique({
    where: { id: sessionId },
    select: { activeOrganizationId: true },
  });

  return dbSession?.activeOrganizationId || null;
}

/**
 * Get the active organization from a session token
 */
export async function getActiveOrganization(
  sessionToken: string
): Promise<Organization | null> {
  const session = await prisma.session.findUnique({
    where: { token: sessionToken },
    include: {
      user: { include: { members: { include: { organization: true } } } },
    },
  });

  if (!session?.activeOrganizationId) return null;

  return await prisma.organization.findUnique({
    where: { id: session.activeOrganizationId },
  });
}

/**
 * Set the active organization for a session
 * @param sessionId - The session ID (not token)
 * @param orgId - The organization ID to set as active
 */
export async function setActiveOrganization(
  sessionId: string,
  orgId: string
): Promise<void> {
  await prisma.session.update({
    where: { id: sessionId },
    data: { activeOrganizationId: orgId },
  });
}

/**
 * Check if a user is a member of an organization
 */
export async function isOrgMember(
  userId: string,
  orgId: string
): Promise<boolean> {
  const member = await prisma.member.findFirst({
    where: { userId, organizationId: orgId },
  });
  return !!member;
}

/**
 * Get a user's role in an organization
 * Returns null if user is not a member
 */
export async function getUserRoleInOrg(
  userId: string,
  orgId: string
): Promise<string | null> {
  const member = await prisma.member.findFirst({
    where: { userId, organizationId: orgId },
  });
  return member?.role || null;
}

/**
 * Get organization by slug
 */
export async function getOrganizationBySlug(
  slug: string
): Promise<Organization | null> {
  return await prisma.organization.findUnique({
    where: { slug },
  });
}
