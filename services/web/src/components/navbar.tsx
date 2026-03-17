"use client"

import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { NavUser } from "@/components/nav-user"
import { Organization } from "@/generated/prisma/client"
import type { UserInfo } from "@/components/app-sidebar"

interface NavbarProps {
  organization?: Organization
  user?: UserInfo
}

export const Navbar = ({ organization, user }: NavbarProps) => {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b px-4">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
      </div>
      <NavUser organization={organization} user={user} />
    </header>
  )
}
