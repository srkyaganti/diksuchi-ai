"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import {
  IconDatabase,
  IconFileAi,
  IconShieldCheck,
  IconUsers,
  IconHistory,
  IconBook,
} from "@tabler/icons-react";

import { NavMain } from "@/components/nav-main";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { useSession } from "@/lib/auth-client";
import { Organization } from "@/generated/prisma/client";
import { OrganizationSwitcher } from "@/components/org/organization-switcher";

export interface UserInfo {
  name: string | null;
  email: string;
  image: string | null;
  isSuperAdmin: boolean;
}

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  organization?: Organization;
  user?: UserInfo;
}

export function AppSidebar({ organization, user: userProp, ...props }: AppSidebarProps) {
  const { data: session } = useSession();

  // Use server-provided user prop if available, otherwise fall back to client session
  const user = userProp ?? (session ? {
    name: session.user.name || null,
    email: session.user.email,
    image: session.user.image || null,
    isSuperAdmin: !!(session.user as any).isSuperAdmin,
  } : null);

  // If organization context exists, use org-scoped URLs
  const baseNavItems = organization
    ? [
        {
          title: "Chat",
          url: `/org/${organization.slug}/chat`,
          icon: IconFileAi,
        },
        {
          title: "Data Library",
          url: `/org/${organization.slug}/data-library`,
          icon: IconDatabase,
        },
        {
          title: "Members",
          url: `/org/${organization.slug}/members`,
          icon: IconUsers,
        },
        {
          title: "Chat History",
          url: `/org/${organization.slug}/chat-history`,
          icon: IconHistory,
        },
        {
          title: "Documentation",
          url: "/docs",
          icon: IconBook,
          external: true,
        },
      ]
    : [
        {
          title: "Chat",
          url: "/chat",
          icon: IconFileAi,
        },
        {
          title: "Data Library",
          url: "/data-library",
          icon: IconDatabase,
        },
      ];

  const navItems = user?.isSuperAdmin
    ? [
        ...baseNavItems,
        {
          title: "Admin",
          url: "/admin",
          icon: IconShieldCheck,
        },
      ]
    : baseNavItems;

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <div className="p-2">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg font-bold">Diksuchi</span>
            <span className="text-muted-foreground font-light">|</span>
            <Image
              src="/avision_logo.png"
              alt="AVision Systems"
              width={90}
              height={28}
              className="h-6 w-auto object-contain"
            />
          </Link>
        </div>
        {organization && (
          <OrganizationSwitcher currentOrg={organization} />
        )}
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navItems} />
      </SidebarContent>
    </Sidebar>
  );
}
