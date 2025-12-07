"use client";

import { useState } from "react";
import { useSession, updateUser } from "@/lib/auth-client";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export function ProfileTab() {
  const { data: session } = useSession();
  const [name, setName] = useState(session?.user?.name || "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const user = session?.user as any;
  const initials = user?.name
    ?.split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase() || user?.email?.[0]?.toUpperCase() || "U";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast.error("Name cannot be empty");
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await updateUser({
        name: name.trim(),
      });

      if (result.error) {
        throw new Error(result.error.message || "Failed to update profile");
      }

      toast.success("Profile updated successfully");
      setName(name.trim());
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update profile");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Profile Information</CardTitle>
        <CardDescription>
          View and manage your account profile
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="space-y-6">
            {/* Avatar Display */}
            <div className="flex items-center gap-4">
              <Avatar className="h-20 w-20">
                <AvatarImage
                  src={user?.image || undefined}
                  alt={user?.name || ""}
                />
                <AvatarFallback className="text-lg">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="space-y-1">
                <p className="text-sm font-medium">Avatar</p>
                <p className="text-sm text-muted-foreground">
                  Your profile picture cannot be changed at this time
                </p>
              </div>
            </div>

            {/* Name Input */}
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                required
              />
              <p className="text-xs text-muted-foreground">
                Your display name visible to others
              </p>
            </div>

            {/* Email Display (Read-only) */}
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={user?.email || ""}
                disabled
                readOnly
              />
              <p className="text-xs text-muted-foreground">
                Email cannot be changed
              </p>
            </div>

            {/* Submit Button */}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
