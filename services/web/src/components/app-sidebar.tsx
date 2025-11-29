"use client"

import * as React from "react"
import {
  IconDatabase,
  IconFileAi,
  IconShieldCheck,
} from "@tabler/icons-react"

import { NavMain } from "@/components/nav-main"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
} from "@/components/ui/sidebar"
import { useSession } from "@/lib/auth-client"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { data: session } = useSession()
  const user = session?.user as any

  const navItems = [
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
  ]

  // Add admin link for super admins
  if (user?.isSuperAdmin) {
    navItems.push({
      title: "Admin",
      url: "/admin",
      icon: IconShieldCheck,
    })
  }

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarContent>
        <NavMain items={navItems} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
