import prisma from "@/lib/prisma";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-dynamic";

export default async function UsersPage() {
  const users = await prisma.user.findMany({
    include: {
      members: {
        include: {
          organization: true,
        },
      },
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">Manage all system users</p>
        </div>
      </div>

      <div className="grid gap-4">
        {users.map((user) => (
          <Card key={user.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{user.name || "Unnamed User"}</CardTitle>
                  <CardDescription>{user.email}</CardDescription>
                </div>
                <div className="flex gap-2">
                  {(user as any).isSuperAdmin && (
                    <Badge variant="destructive">Super Admin</Badge>
                  )}
                  {(user as any).mustChangePassword && (
                    <Badge variant="secondary">Must Change Password</Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                <p className="text-muted-foreground">
                  Organizations: {user.members.length}
                </p>
                {user.members.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {user.members.map((member) => (
                      <li key={member.id}>
                        {member.organization.name} - {member.role}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>
        ))}

        {users.length === 0 && (
          <Card>
            <CardContent className="flex min-h-[200px] items-center justify-center">
              <p className="text-muted-foreground">No users found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
