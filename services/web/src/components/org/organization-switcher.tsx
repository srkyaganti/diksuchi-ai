"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { IconSwitchHorizontal } from "@tabler/icons-react";
import { Organization } from "@/generated/prisma/client";

interface OrganizationSwitcherProps {
  currentOrg: Organization;
}

export function OrganizationSwitcher({
  currentOrg,
}: OrganizationSwitcherProps) {
  const router = useRouter();

  return (
    <div className="p-2">
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="text-sm font-semibold">{currentOrg.name}</p>
          <p className="text-xs text-muted-foreground">@{currentOrg.slug}</p>
        </div>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="w-full"
        onClick={() => router.push("/select-organization")}
      >
        <IconSwitchHorizontal className="mr-2 h-4 w-4" />
        Switch Organization
      </Button>
    </div>
  );
}
