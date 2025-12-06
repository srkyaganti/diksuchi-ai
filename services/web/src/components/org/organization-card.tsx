"use client";

import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Organization } from "@/generated/prisma/client";

interface OrganizationCardProps {
  organization: Organization & { _count?: { members: number }; members?: any[] };
  userRole?: string;
  redirectPath: string;
}

export function OrganizationCard({
  organization,
  userRole,
  redirectPath,
}: OrganizationCardProps) {
  const router = useRouter();

  const handleSelect = async () => {
    // Switch active organization
    const res = await fetch(`/api/organizations/${organization.id}/switch`, {
      method: "POST",
    });

    if (res.ok) {
      // Redirect to org page
      router.push(`/org/${organization.slug}/${redirectPath}`);
      router.refresh();
    } else {
      console.error("Failed to switch organization");
    }
  };

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={handleSelect}
    >
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{organization.name}</CardTitle>
          {userRole && <Badge variant="secondary">{userRole}</Badge>}
        </div>
        <CardDescription>
          {organization._count?.members || 0} members
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button className="w-full">Enter Organization</Button>
      </CardContent>
    </Card>
  );
}
