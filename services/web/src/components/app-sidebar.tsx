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

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  organization?: Organization;
}

export function AppSidebar({ organization, ...props }: AppSidebarProps) {
  const { data: session } = useSession();
  const user = session?.user as any;

  // If organization context exists, use org-scoped URLs
  const navItems = organization
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

  // Add admin link for super admins
  if (user?.isSuperAdmin) {
    navItems.push({
      title: "Admin",
      url: "/admin",
      icon: IconShieldCheck,
    });
  }

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
