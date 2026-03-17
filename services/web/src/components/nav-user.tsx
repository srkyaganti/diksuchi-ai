"use client"

import {
  IconDotsVertical,
  IconLogout,
  IconSettings,
} from "@tabler/icons-react"
import { useRouter } from "next/navigation"
import { Organization } from "@/generated/prisma/client"
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useSession, signOut } from "@/lib/auth-client"
import type { UserInfo } from "@/components/app-sidebar"

interface NavUserProps {
  organization?: Organization
  user?: UserInfo
}

export function NavUser({ organization, user: userProp }: NavUserProps) {
  const { data: session } = useSession()
  const router = useRouter()

  // Use server-provided user prop if available, otherwise fall back to client session
  const user = userProp ?? (session ? {
    name: session.user.name || null,
    email: session.user.email,
    image: session.user.image || null,
    isSuperAdmin: false,
  } : null)

  if (!user) {
    return (
      <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
        <div className="h-8 w-8 rounded-lg bg-muted animate-pulse" />
      </div>
    )
  }

  const initials = user.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() || user.email[0].toUpperCase()

  const handleSignOut = async () => {
    await signOut()
    router.push("/login")
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="User menu"
          tabIndex={0}
        >
          <Avatar className="h-8 w-8 rounded-lg grayscale">
            <AvatarImage src={user.image || undefined} alt={user.name || ""} />
            <AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
          </Avatar>
          <div className="hidden md:grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-medium">{user.name}</span>
            <span className="text-muted-foreground truncate text-xs">
              {user.email}
            </span>
          </div>
          <IconDotsVertical className="ml-auto size-4 hidden md:block" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className="min-w-56 rounded-lg"
        side="bottom"
        align="end"
        sideOffset={4}
      >
        <DropdownMenuLabel className="p-0 font-normal">
          <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
            <Avatar className="h-8 w-8 rounded-lg">
              <AvatarImage src={user.image || undefined} alt={user.name || ""} />
              <AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
            </Avatar>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">{user.name}</span>
              <span className="text-muted-foreground truncate text-xs">
                {user.email}
              </span>
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => router.push(organization ? `/org/${organization.slug}/settings` : "/settings")}>
          <IconSettings />
          Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleSignOut}>
          <IconLogout />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
