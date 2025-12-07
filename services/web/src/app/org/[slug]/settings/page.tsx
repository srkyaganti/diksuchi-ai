"use client";

import { useSession } from "@/lib/auth-client";
import { ProfileTab } from "@/components/settings/profile-tab";
import { PasswordTab } from "@/components/settings/password-tab";

export default function SettingsPage() {
  const { data: session } = useSession();

  if (!session) {
    return null;
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings. These settings are global and apply across all organizations.
        </p>
      </div>

      <div className="space-y-6">
        <ProfileTab />
        <PasswordTab />
      </div>
    </div>
  );
}
