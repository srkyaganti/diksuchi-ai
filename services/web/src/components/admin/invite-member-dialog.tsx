"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { IconUserPlus } from "@tabler/icons-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";

interface InviteMemberDialogProps {
  organizationId: string;
}

export function InviteMemberDialog({ organizationId }: InviteMemberDialogProps) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<string>("member");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setGeneratedPassword(null);

    try {
      const response = await fetch("/api/admin/invite-member", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          name,
          role,
          organizationId,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Failed to invite member");
      }

      const data = await response.json();
      setGeneratedPassword(data.password);

      toast.success("Member invited successfully");
      router.refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to invite member");
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setEmail("");
    setName("");
    setRole("member");
    setGeneratedPassword(null);
    setIsSubmitting(false);
  };

  const copyPassword = () => {
    if (generatedPassword) {
      navigator.clipboard.writeText(generatedPassword);
      toast.success("Password copied to clipboard");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <IconUserPlus className="mr-2 h-4 w-4" />
          Invite Member
        </Button>
      </DialogTrigger>
      <DialogContent>
        {!generatedPassword ? (
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Invite Member</DialogTitle>
              <DialogDescription>
                Invite a new member to this organization
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="role">Role</Label>
                <Select value={role} onValueChange={setRole}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="owner">Owner</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="member">Member</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Inviting..." : "Invite Member"}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Member Invited Successfully</DialogTitle>
              <DialogDescription>
                Share this temporary password with the new member
              </DialogDescription>
            </DialogHeader>

            <div className="py-4">
              <Card className="bg-muted">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-xs text-muted-foreground">Email</Label>
                      <p className="font-medium">{email}</p>
                    </div>
                    <div>
                      <Label className="text-xs text-muted-foreground">Temporary Password</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="flex-1 rounded bg-background px-3 py-2 font-mono text-sm">
                          {generatedPassword}
                        </code>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={copyPassword}
                        >
                          Copy
                        </Button>
                      </div>
                    </div>
                    <div className="rounded-md bg-yellow-500/10 border border-yellow-500/20 p-3">
                      <p className="text-sm text-yellow-900 dark:text-yellow-100">
                        ⚠️ This password will only be shown once. The user will be required to change it on first login.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
