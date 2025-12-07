"use client";

import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { ProfileTab } from "@/components/settings/profile-tab";
import { PasswordTab } from "@/components/settings/password-tab";

export default function SettingsPage() {
  const { data: session } = useSession();
  const router = useRouter();

  if (!session) {
    return null;
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <ProfileTab />
        </TabsContent>

        <TabsContent value="password" className="space-y-4">
          <PasswordTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
